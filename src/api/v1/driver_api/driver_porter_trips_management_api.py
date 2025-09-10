from fastapi import APIRouter , Depends, Header, Request 
from sqlalchemy import asc, desc, func, select
from auth.dependencies import driver_role_required
from config.exceptions import NotFoundError
from db.database_operations import  get_tuple_instance, insert_into_table
from integrations.location_service import get_distance
from models.assignment_mapping_models import MfoVehicleMapping
from models.costing_models import VehicleCosting
from models.driver_models import DriverMain
from models.hotspot_routes_models import HotspotRoutes
from models.task_management_models import TaskScheduleMapping, Tasks
from models.vehicle_models import VehicleMain
from schemas.v1.standard_schema import standard_success_response
from schemas.v1.driver_schemas.driver_porter_schema import (
    get_porter_trip_response, porter_trip_off_request,
    porter_trip_off_response, porter_trip_on_request,
    porter_trip_on_response
)
from settings.static_data_settings import static_table_settings
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from models.porter_models import AvaronnPorterTrip
from utils.driver_incentive_utils import get_incentive_points
from utils.response import success_response
from utils.time_utils import convert_utc_to_ist, get_utc_time
from shapely.geometry import Point
from geoalchemy2.shape import from_shape 

driver_porter_trips_management_router = APIRouter()







@driver_porter_trips_management_router.post("/porterTripOn" , response_model= standard_success_response[porter_trip_on_response] , status_code = 201)
async def porterTripOn(request:Request,
                       req: porter_trip_on_request,
                       driver_uuid = Depends(driver_role_required()),
                       session:AsyncSession = Depends(get_async_db),
                       session_id: str = Header(..., alias="session-id"),
                       device_id: str = Header(..., alias="device-id")
                       ):
    vehicle_mapping_instance = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" :driver_uuid , "is_enable" : True})
    if not vehicle_mapping_instance:
        raise NotFoundError("No currently assigned vehicle")
    
    
    query = select(
        TaskScheduleMapping.schedule_uuid
    ).join(
        Tasks, TaskScheduleMapping.task_uuid == Tasks.task_uuid
    ).where(
        Tasks.vehicle_uuid == vehicle_mapping_instance.vehicle_uuid
    ).order_by(
        desc(Tasks.id) 
    ).limit(1)

    result = await session.execute(query)
    schedule_uuid = result.scalar()
    if not schedule_uuid:
        raise NotFoundError("No Schedule Available")
    start_location = from_shape(Point(req.driver_lng, req.driver_lat), srid=4326)
    data = {
        "driver_uuid" : driver_uuid,
        "vehicle_uuid" : vehicle_mapping_instance.vehicle_uuid,
        "schedule_uuid" : schedule_uuid,
        "trip_on_lat" : req.driver_lat,
        "trip_on_lng" : req.driver_lng,
        "trip_on_location" : start_location,
        "trip_on_time" : get_utc_time()
    }
    porter_tip_instance = await insert_into_table(session , AvaronnPorterTrip , data)
    porter_dict = {c.name: getattr(porter_tip_instance, c.name) for c in porter_tip_instance.__table__.columns}
    
    last_hotspot_instance = await get_tuple_instance(session ,
                                                     HotspotRoutes,
                                                     {'driver_uuid': driver_uuid},
                                                     order_by=[desc(HotspotRoutes.id)],
                                                     limit=1 
                                                     )
    if last_hotspot_instance:
        if not last_hotspot_instance.reached_hotspot:
            last_hotspot_instance.reached_hotspot = True
            last_hotspot_instance.reached_hotspot_timestamp = get_utc_time()
            last_hotspot_instance.got_trip = True
            last_hotspot_instance.avaronn_porter_trip_uuid = porter_dict['avaronn_porter_trip_uuid']
            last_hotspot_instance.got_trip_at = get_utc_time()
            
    
    points_earned  = 0.0
    
    await session.commit()
    await session.close()
    
    
    data_res =  porter_trip_on_response(
        avaronn_porter_trip_uuid = porter_dict['avaronn_porter_trip_uuid'],
        points_earned = points_earned
    )
    return success_response(request , data_res , message = "Porter Trip on Successfully")
            
     




@driver_porter_trips_management_router.put("/porterTripOff" , response_model= standard_success_response[porter_trip_off_response] , status_code = 200)
async def porterTripOff(request:Request,
                        req:porter_trip_off_request,
                        driver_uuid = Depends(driver_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    trip_off_time = get_utc_time()
    
    porter_data = await get_tuple_instance(session , AvaronnPorterTrip , {'avaronn_porter_trip_uuid' : req.avaronn_porter_trip_uuid})
    if not porter_data:
        raise NotFoundError("No Porter Trip available to turn off")
    
    
    interval = trip_off_time - porter_data.trip_on_time
    vehicle_costing_instance = await get_tuple_instance(session , VehicleCosting , {"vehicle_uuid" : porter_data.vehicle_uuid , "is_enable":True})
    
    fuel_based_costing_dict = static_table_settings.static_table_data['FUEL_BASED_COSTING']
    
    per_km_cost = fuel_based_costing_dict[vehicle_costing_instance.fuel_based_costing_uuid]
    
    start_lat = porter_data.trip_on_lat
    start_lng = porter_data.trip_on_lng
    
    end_lat = req.driver_lat
    end_lng = req.driver_lng
    
    
    end_location = from_shape(Point(req.driver_lng, req.driver_lat), srid=4326)
    porter_data.trip_off_lat = end_lat
    porter_data.trip_off_lng = end_lng
    porter_data.trip_off_time = trip_off_time
    porter_data.total_trip_time = interval
    porter_data.trip_off_location = end_location
    
    distance_in_km = await get_distance(f"{start_lat} , {start_lng}" , f"{end_lat} , {end_lng}")
    if distance_in_km:
        distance_in_km = distance_in_km[0] if distance_in_km[0] else 0
    else:
        distance_in_km = 10
    vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : porter_data.vehicle_uuid})
    porter_data.expected_distance_km = distance_in_km
    porter_data.expected_earning = distance_in_km * 30 if vehicle_instance.category[0] == "3" else distance_in_km*40
    porter_data.expected_cost = distance_in_km * per_km_cost
    
    attributes = list(porter_trip_off_response.model_fields.keys()) 
    porter_dict = {key: getattr(porter_data, key) for key in attributes if hasattr(porter_data, key)}
    porter_dict["points_earned"] , porter_dict["incentive_earned"] = await get_incentive_points(session ,driver_uuid  , porter_data.vehicle_uuid , vehicle_costing_instance.mfo_uuid ,  "Trip off" , distance_in_km)
    
    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : driver_uuid , "is_enable" : True})
    driver_instance.assignments_completed +=1
    driver_instance.distance_driven += distance_in_km
    await session.commit()
    await session.refresh(porter_data)
    await session.close()
    

    porter_dict['trip_on_time'] = convert_utc_to_ist(porter_dict['trip_on_time'])
    porter_dict['trip_off_time'] = convert_utc_to_ist(porter_dict['trip_off_time'])
    
    
    data_res =  porter_trip_off_response(**porter_dict)
    return success_response(request , data_res , message = "Porter Trip off Successfully")
    




@driver_porter_trips_management_router.get("/getPorterTrips" , response_model= standard_success_response[get_porter_trip_response] , status_code = 200)
async def getPorterTrips(request:Request,
                         driver_uuid = Depends(driver_role_required()),
                         session:AsyncSession = Depends(get_async_db),
                         session_id: str = Header(..., alias="session-id"),
                         device_id: str = Header(..., alias="device-id")
                         ):
    query = select(AvaronnPorterTrip).where(
            AvaronnPorterTrip.driver_uuid == driver_uuid,
            func.DATE(AvaronnPorterTrip.trip_on_time) == func.DATE(get_utc_time())
        ).order_by(
            asc(AvaronnPorterTrip.id)
        )

    result = await session.execute(query)
    trips = result.scalars().all()
    current_trip = None
    trip_list = []
    for trip in trips:
        trip_data = {
            "trip_uuid" : trip.avaronn_porter_trip_uuid,
            "trip_on_time": convert_utc_to_ist(trip.trip_on_time) if trip.trip_on_time else None,
            "trip_off_time": convert_utc_to_ist(trip.trip_off_time) if trip.trip_off_time else None,
            "total_trip_time": str(trip.total_trip_time) if trip.total_trip_time else None
        }
        if trip_data['trip_off_time'] is None:
            current_time = get_utc_time()
            interval = current_time - trip.trip_on_time
            total_seconds = int(interval.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            trip_data['current_trip_running_time'] = f"{hours:02}:{minutes:02}:{seconds:02}"
            current_trip = trip_data
        else:
            trip_list.append(trip_data)
    
    await session.close()
    data_res =  get_porter_trip_response(
        current_trip =  current_trip,
        completed_trips = trip_list
        )
    return success_response(request , data_res , message = "Porter Trips data get Successfully")
    
        