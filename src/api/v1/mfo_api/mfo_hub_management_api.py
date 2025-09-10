from fastapi import APIRouter , Depends, Header, Request
from sqlalchemy import desc
from auth.dependencies import mfo_role_required
from config.exceptions import ConflictError
from integrations.location_service import generate_google_maps_link, get_location_details_from_pincode
from models.vehicle_hub_models import HubAddressBook, VehicleHubMapping
from schemas.v1.mfo_schemas.mfo_hub_management_schema import add_new_hub_request, add_new_hub_response, add_vehicle_to_hub_request, add_vehicle_to_hub_response, get_all_hubs_response, remove_vehicle_from_hub_request, remove_vehicle_from_hub_response, vehicle_hubs
from schemas.v1.standard_schema import standard_success_response
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from db.database_operations import fetch_from_table, get_tuple_instance, insert_into_table
from utils.response import success_response
from shapely.geometry import Point
from geoalchemy2.shape import from_shape

from utils.time_utils import get_utc_time 

mfo_hub_management_router = APIRouter()





@mfo_hub_management_router.post("/addNewHub" , response_model = standard_success_response[add_new_hub_response] )
async def addNewHub(request:Request,
                    req:add_new_hub_request,
                    mfo_uuid = Depends(mfo_role_required()),
                    session:AsyncSession = Depends(get_async_db),
                    session_id: str = Header(..., alias="session-id"),
                    device_id: str = Header(..., alias="device-id")
                    ):
    
    google_maps_link = generate_google_maps_link(req.hub_lat , req.hub_lng)
    hub_location = from_shape(Point(req.hub_lng, req.hub_lat), srid=4326)
    location_details = await get_location_details_from_pincode(req.hub_pincode)
    
    hub_data = {
        "hub_name" : req.hub_name,
        "mfo_uuid" : mfo_uuid,
        "hub_lat" : req.hub_lat,
        "hub_lng" : req.hub_lng, 
        "hub_location" : hub_location,
        "hub_area" : location_details["area"] if location_details else None,
        "hub_city" : location_details["city"] if location_details else None,
        "hub_state" : location_details["state"] if location_details else None,
        "hub_pincode" : req.hub_pincode , 
        "hub_country" : location_details["country"] if location_details else None,
        "hub_full_address" : req.hub_address ,
        "hub_google_location" : google_maps_link 
    }
     
    hub_instance = await insert_into_table(session , HubAddressBook , hub_data)
    
    response_data = {
        "hub_address_book_uuid" : hub_instance.hub_address_book_uuid,
        "hub_name" : req.hub_name,
        "hub_pincode" : req.hub_pincode,
        "hub_full_address" : req.hub_address,
        "hub_google_location" : google_maps_link
    }
    
    data_res = add_new_hub_response(**response_data)
    await session.commit()
    await session.close()
    return success_response(request , data_res , message = "New hub added successfully")




@mfo_hub_management_router.post("/addVehicleToHub" , response_model = standard_success_response[add_vehicle_to_hub_response] )
async def addVehicleToHub(request:Request,
                    req:add_vehicle_to_hub_request,
                    mfo_uuid = Depends(mfo_role_required()),
                    session:AsyncSession = Depends(get_async_db),
                    session_id: str = Header(..., alias="session-id"),
                    device_id: str = Header(..., alias="device-id")
                    ):
    mapping_data = {
        "hub_address_book_uuid": req.hub_address_book_uuid,
        "mfo_uuid" : mfo_uuid,
        "vehicle_uuid" : req.vehicle_uuid,
        "is_enable" : True
    }
    already_exist_instance = await get_tuple_instance(session , VehicleHubMapping , mapping_data)
    if already_exist_instance:
        raise ConflictError("Vehicle Already added to this hub")
    await insert_into_table(session , VehicleHubMapping , mapping_data)
    response_data = {
        "hub_address_book_uuid" : req.hub_address_book_uuid,
        "vehicle_uuid" : req.vehicle_uuid
    }
    data_res = add_vehicle_to_hub_response(**response_data)
    await session.commit()
    await session.close()
    return success_response(request , data_res , message = "Vehicle Added to hub successfully")







@mfo_hub_management_router.get("/getAllHubs" , response_model = standard_success_response[get_all_hubs_response] )
async def getAllHubs(request:Request,
                    mfo_uuid = Depends(mfo_role_required()),
                    session:AsyncSession = Depends(get_async_db),
                    session_id: str = Header(..., alias="session-id"),
                    device_id: str = Header(..., alias="device-id")
                    ):
    all_hubs_list = []
    hub_data = await fetch_from_table(session , HubAddressBook , None , {"mfo_uuid" : mfo_uuid ,"is_enable" :True})
    
    for hub in hub_data:
        vehicle_on_hub_mapppings = await fetch_from_table(session , VehicleHubMapping , None ,{"hub_address_book_uuid" : hub["hub_address_book_uuid"]  , "mfo_uuid" : mfo_uuid , "is_enable" : True})
        vehicles_on_hub = len(vehicle_on_hub_mapppings)
        all_hubs_list.append(
            vehicle_hubs(
                hub_address_book_uuid = hub["hub_address_book_uuid"],
                hub_name = hub["hub_name"],
                hub_pincode = hub["hub_pincode"],
                hub_full_address = hub["hub_full_address"],
                hub_google_location = hub["hub_google_location"],
                vehicles_on_hub = vehicles_on_hub,
                lat = ["hub_lat"],
                lng = ["hub_lng"]
                )
            )
    data_res = get_all_hubs_response(all_hubs = all_hubs_list)
    
    await session.commit()
    await session.close()
    return success_response(request , data_res , message = "Get all hubs successfully")





@mfo_hub_management_router.get("/removeVehicleFromHub" , response_model = standard_success_response[remove_vehicle_from_hub_response] )
async def removeVehicleFromHub(request:Request,
                     req:remove_vehicle_from_hub_request,
                    mfo_uuid = Depends(mfo_role_required()),
                    session:AsyncSession = Depends(get_async_db),
                    session_id: str = Header(..., alias="session-id"),
                    device_id: str = Header(..., alias="device-id")
                    ):
    
    unique_attributes = {
    "hub_address_book_uuid" : req.hub_address_book_uuid,
    "mfo_uuid" : mfo_uuid,
    "vehicle_uuid" : req.vehicle_uuid,
    "is_enable" : True
    }
    vehicle_hub_mapping_instance = await get_tuple_instance(session ,
                                                            VehicleHubMapping ,
                                                            unique_attributes ,
                                                            order_by=[desc(VehicleHubMapping.id)],
                                                            limit = 1) 
    if vehicle_hub_mapping_instance:
        vehicle_hub_mapping_instance.is_enable = False
        vehicle_hub_mapping_instance.hub_changed_at = get_utc_time()
    
    data_res = remove_vehicle_from_hub_response(removed_status=True)
    await session.commit()
    await session.close()
    return success_response(request , data_res , message = "Vehicle removed from hub successfully")



# @mfo_hub_management_router.get("/GetAllVehiclesOnHub" , response_model = standard_success_response[remove_vehicle_from_hub_response] )
# async def GetAllVehiclesOnHub_api(request:Request,
#                      req:remove_vehicle_from_hub_request,
#                     mfo_uuid = Depends(mfo_role_required()),
#                     session:AsyncSession = Depends(get_async_db),
#                     session_id: str = Header(..., alias="session-id"),
#                     device_id: str = Header(..., alias="device-id")
#                     ):
    
#     unique_attributes = {
#     "hub_address_book_uuid" : req.hub_address_book_uuid,
#     "mfo_uuid" : mfo_uuid,
#     "vehicle_uuid" : req.vehicle_uuid,
#     "is_enable" : True
#     }
#     vehicle_hub_mapping_instance = await get_tuple_instance(session ,
#                                                             VehicleHubMapping ,
#                                                             unique_attributes ,
#                                                             order_by=[desc(VehicleHubMapping.id)],
#                                                             limit = 1) 
#     if vehicle_hub_mapping_instance:
#         vehicle_hub_mapping_instance.is_enable = False
#         vehicle_hub_mapping_instance.hub_changed_at = get_utc_time()
    
#     data_res = remove_vehicle_from_hub_response(removed_status=True)
#     await session.commit()
#     await session.close()
#     return success_response(request , data_res , message = "Vehicle removed from hub successfully")