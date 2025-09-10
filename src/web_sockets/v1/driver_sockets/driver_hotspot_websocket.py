import json
from fastapi import APIRouter, Depends, WebSocket
from math import radians, cos, sin, sqrt, atan2
import polyline
import httpx
from auth.jwt import verify_token
from config.exceptions import ForbiddenError, UnauthorizedError
from db.database_operations import get_tuple_instance, insert_into_table
from db.db import get_async_session_factory
from models.hotspot_routes_models import HotspotRoutedeviationLogs, HotspotRoutes
from utils.time_utils import get_utc_time
from settings.credential_settings import credential_setting
import asyncio


# async def haversine(lat1, lon1, lat2, lon2):
#     R = 6371000  
#     phi1, phi2 = radians(lat1), radians(lat2)
#     dphi = radians(lat2 - lat1)
#     dlambda = radians(lon2 - lon1)
#     a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
#     return 2 * R * atan2(sqrt(a), sqrt(1 - a))

# async def get_remaining_distance(current_lat, current_lng, path_coords):
#     async def distance(p1, p2):
#         dist = await haversine(p1[0], p1[1], p2[0], p2[1])
#         return dist

    
#     distances = [distance((current_lat, current_lng), (lat, lng)) for lat, lng in path_coords]
#     closest_index = distances.index(min(distances))

#     remaining_distance = 0
#     for i in range(closest_index, len(path_coords) - 1):
#         remaining_distance += distance(path_coords[i], path_coords[i+1])

#     return remaining_distance


async def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))

async def distance(p1, p2):
    return await haversine(p1[0], p1[1], p2[0], p2[1])

async def get_remaining_distance(current_lat, current_lng, path_coords):
    # Compute distances from current location to each point in path_coords
    distance_tasks = [
        distance((current_lat, current_lng), (lat, lng))
        for lat, lng in path_coords
    ]
    all_distances = await asyncio.gather(*distance_tasks)

    # Find the index of the closest point
    closest_index = all_distances.index(min(all_distances))

    # Now compute remaining distance from closest_index onwards
    segment_tasks = [
        distance(path_coords[i], path_coords[i+1])
        for i in range(closest_index, len(path_coords) - 1)
    ]
    segment_distances = await asyncio.gather(*segment_tasks)

    return sum(segment_distances)



async def get_reroute(driver_lat , driver_lng , destination_lat , destination_lng):
    origin = f"{driver_lat},{driver_lng}"
    destination = f"{destination_lat},{destination_lng}"
    async with httpx.AsyncClient() as client:
        response = await client.get(
        "https://maps.googleapis.com/maps/api/directions/json",
        params={
        "origin": origin,
        "destination": destination,
        "mode": "driving",
        "departure_time": "now",
        "traffic_model": "best_guess",
        "key": credential_setting.google_map_api_key
        }
        )

        if response.status_code == 200:
            directions = response.json()
            if directions['status'] != 'OK' or not directions.get('routes'):
                return None

            route = directions['routes'][0]
            leg = route['legs'][0]
            polyline_data = route['overview_polyline']['points']
            coords = polyline.decode(polyline_data)
            polylines = [{"lat" : c[0] , "lng" : c[1]} for c in coords]

            return[{
                "status" : "route changed",
                "message" : "Rerouting...",
                "polyline": polylines,
                "eta": leg['duration_in_traffic']['text'],
                "distance": f"{round(leg['distance']['value']/1000 , 2)} km"
            } , coords]
        
    return None



THRESHOLD_METERS = 80

driver_hotspot_websocket_router = APIRouter()

connected_clients = []

@driver_hotspot_websocket_router.websocket("/hotspotWS")
async def handler(websocket:WebSocket , session_factory = Depends(get_async_session_factory)):
    token = websocket.headers.get("Bearer")
    if not token:
        raise UnauthorizedError()
    
    payload = await verify_token(token)

    if not payload:
        raise ForbiddenError("Invalid token")
    
    await websocket.accept()
    connected_clients.append(websocket)
    coordinates = None
    route_instance = None
    prev_lat = None
    prev_lng = None
    repeatation_counter = 0
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            driver_lat = data["driver_lat"]
            driver_lng = data["driver_lng"]
            hotspot_route_uuid = data['hotspot_route_uuid']
            
            
            if not coordinates:
                async with session_factory() as db:
                    route_instance = await get_tuple_instance(db , HotspotRoutes ,{"hotspot_route_uuid" : hotspot_route_uuid})
                    overview_poly = route_instance.route_overview_polyline
                    coordinates = polyline.decode(overview_poly)
                
            
            response = None

            if round(driver_lat , 5) == prev_lat and round(driver_lng, 5) == prev_lng:
                repeatation_counter += 1
            
            else:
                
                prev_lat = round(driver_lat , 5)
                prev_lng =  round(driver_lng, 5)
                repeatation_counter = 0
            
            distance = await get_remaining_distance(driver_lat, driver_lng, coordinates)
            if repeatation_counter >= 15:
                response = {"status": "alert",
                            "message": "Vehicle Stopped" ,
                            "eta" : f"{round(distance/500.0 , 2)} mins",
                            "distance" : f"{round(distance/1000 , 2)} km"}
                await websocket.send_json(response)
                repeatation_counter = 0  

            overview_navigation = [{"lat": lat, "lng": lng} for lat, lng in coordinates]
            
            destination_lat = overview_navigation[-1]["lat"]
            destination_lng = overview_navigation[-1]["lng"]

            DESTINATION_THRESHOLD_METERS = 30
            shortest_distance = float('inf')
            
            at_destination = await  haversine(driver_lat, driver_lng, destination_lat, destination_lng) < DESTINATION_THRESHOLD_METERS
            on_route = False
            if not at_destination:
                for nav in overview_navigation:
                    dist = await haversine(driver_lat, driver_lng, nav["lat"], nav["lng"])
                    shortest_distance = min(shortest_distance , dist)
                on_route =  shortest_distance< THRESHOLD_METERS
                    
            if at_destination:
                async with session_factory() as db:
                    route_instance = await get_tuple_instance(db, HotspotRoutes, {"hotspot_route_uuid": hotspot_route_uuid})
                    route_instance.reached_hotspot = True
                    route_instance.reached_hotspot_timestamp = get_utc_time()
                    await db.commit()
                response = {"status" : "success" ,
                            "message" : "You have reached your destination.",
                            "eta" : f"{round(distance/500.0 , 2)} mins",
                            "distance" : f"{round(distance/1000 , 2)} km"}
                await websocket.send_json(response)
                break
            elif on_route:
                response = {"status": "ok",
                            "message": "On route",
                            "eta" : f"{round(distance/500.0 , 2)} mins",
                            "distance" : f"{round(distance/1000 , 2)} km"} #30km/hr = 500 mt/min
            else:
                new_route = await get_reroute(driver_lat , driver_lng , destination_lat , destination_lng)
                if new_route:
                    async with session_factory() as db:
                        log_data = {
                            "driver_uuid" : payload["driver_uuid"],
                            "hotspot_route_uuid" : hotspot_route_uuid,
                            "deviated_lat" : driver_lat,
                            "deviated_lng" : driver_lng,
                            "deviated_distance_mt" : shortest_distance
                        }
                        await insert_into_table(db , HotspotRoutedeviationLogs , log_data)
                        await db.commit()
                    response = new_route[0]
                    coordinates = new_route[1]
                else:
                    response = {"status": "warning",
                                "message": "Off route! Please return to the navigation path.",
                                "eta" : f"{round(distance/500.0 , 2)} mins",
                                "distance" : f"{round(distance/1000 , 2)} km"}  #30km/hr = 500 mt/min
            await websocket.send_json(response)
    except Exception as e:
        print("WebSocket error:", e)
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        await websocket.close()