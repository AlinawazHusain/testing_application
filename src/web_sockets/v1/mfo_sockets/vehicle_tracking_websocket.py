import asyncio
import json
from fastapi import APIRouter, Depends, WebSocket
import time
from sqlalchemy import desc
from auth.jwt import verify_token
from config.exceptions import ForbiddenError, UnauthorizedError
from db.database_operations import get_tuple_instance
from db.db import get_async_session_factory
from helpers.mfo_helpers.mfo_vehicle_helpers import get_vehicle_current_activity
from integrations.location_service import get_location_name
from models.can_data_model import CANData
from models.vehicle_models import VehicleLocation, VehicleMain
from utils.time_utils import convert_utc_to_ist, get_utc_time
from utils.vehicle_activity_rule_engine import get_vehile_activity
from settings.static_data_settings import static_table_settings




vehicle_tracking_websocket_router = APIRouter()

connected_clients = []

@vehicle_tracking_websocket_router.websocket("/vehicleTrackingWS")
async def handler(websocket:WebSocket , session_factory = Depends(get_async_session_factory)):
    token = websocket.headers.get("Bearer")
    if not token:
        raise UnauthorizedError()
    
    payload = await verify_token(token)

    if not payload:
        raise ForbiddenError("Invalid token")
    
    await websocket.accept()
    connected_clients.append(websocket)
    vehicle_number = None
    driver_uuid = None
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            vehicle_uuid =  data["vehicle_uuid"]
            response = None
            async with session_factory() as db:
                vehicle_instance = await get_tuple_instance(db , VehicleMain , {"vehicle_uuid" : vehicle_uuid})
                vehicle_number = vehicle_instance.vehicle_number
                driver_uuid = vehicle_instance.driver_uuid
                vehicle_status_dict = static_table_settings.static_table_data["VEHICLE_STATUS"]
    
            while True:
                if vehicle_number:
                    vehicle_location_lat_and_lng = {"lat" : 27.322 , "lng" : 89.00}
                    vehicle_heading_direction = 180.9
                    vehicle_current_soc = 59.0
                    vehilce_speed = 23.0
                    vehicle_km_left = 9.89
                    vehicle_current_status = "Running"
                    vehicle_current_location = "abcdedf"
                    location_updated_at = get_utc_time()
                    async with session_factory() as db:
                            vehicle_location_instance = await get_tuple_instance(db , VehicleLocation ,{"vehicle_number" : vehicle_number} , order_by = [desc(VehicleLocation.id)] , limit = 1)
                            vehicle_can_instance = await get_tuple_instance(db , CANData , {"vehicle_number" : vehicle_number} ,  order_by = [desc(CANData.id)] , limit = 1)
                            if vehicle_location_instance and vehicle_can_instance:
                                vehicle_location_lat_and_lng = {"lat" : vehicle_location_instance.lat , "lng" : vehicle_location_instance.lng}
                                vehilce_speed = vehicle_can_instance.vehicle_speed_value
                                vehicle_heading_direction = vehicle_location_instance.heading
                                vehicle_current_soc = vehicle_can_instance.soc_value
                                vehicle_km_left = round(((vehicle_current_soc/100.0) * 7.7)*9.09 , 2)
                                vehicle_current_status = await get_vehile_activity(db , vehicle_uuid)
                                # await get_vehicle_current_activity(db , vehicle_current_status , vehicle_uuid , driver_uuid)
                                vehicle_current_location = await get_location_name(vehicle_location_lat_and_lng["lat"] , vehicle_location_lat_and_lng["lng"])
                                location_updated_at = convert_utc_to_ist(vehicle_location_instance.created_at)
                                vehicle_instance = await get_tuple_instance(db , VehicleMain , {"vehicle_uuid" : vehicle_uuid})
                                vehicle_status = vehicle_status_dict.get(vehicle_instance.vehicle_status , None)
                                response = {
                                    "vehicle_uuid": vehicle_uuid,
                                    "vehicle_number" : vehicle_number,
                                    "vehicle_status" : vehicle_status,
                                    "vehicle_location_lat_and_lng" : vehicle_location_lat_and_lng,
                                    "vehicle_heading_direction" : vehicle_heading_direction,
                                    "vehicle_current_location" : vehicle_current_location,
                                    "vehicle_current_status" : vehicle_current_status,
                                    "vehicle_current_soc" : vehicle_current_soc,
                                    "vehicle_km_left" : vehicle_km_left,
                                    "vehilce_speed" : vehilce_speed,
                                    "location_updated_at" : location_updated_at.isoformat()
                                }
                            else:
                                response = "Vehicle not integrated"
                    
                    
                    
                    if response:
                        await websocket.send_json(response)
                        
                    await asyncio.sleep(3)
    except Exception as e:
        print("WebSocket error:", e)
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        await websocket.close()