from fastapi import APIRouter, Header, Request , Depends 
from sqlalchemy import desc, func, select
from auth.dependencies import driver_role_required
from config.exceptions import InvalidRequestError, NotFoundError
from db.database_operations import fetch_from_table, get_tuple_instance, insert_into_table
from models.assignment_mapping_models import DriverMfoMapping, DriverVehicleMapping, MfoVehicleMapping
from models.attendace_models import DriverAttendance
from models.driver_models import DriverMain
from models.mfo_models import MfoBusiness, MfoMain
from models.notification_listner_models import NotificationListner
from models.vehicle_models import VehicleMain
from schemas.v1.standard_schema import standard_success_response
from schemas.v1.driver_schemas.driver_get_basic_data_schema import (
    SOS_response, get_docs_data_response,
    get_profile_data_response,
    get_vehicle_data_response, pushNotification_request, pushNotification_response
    )
from settings.static_data_settings import static_table_settings
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from utils.response import success_response
from utils.time_utils import convert_utc_to_ist, get_utc_time



driver_get_basic_data_router = APIRouter()






@driver_get_basic_data_router.get("/getProfileData" , response_model = standard_success_response[get_profile_data_response] , status_code=200)
async def getProfileData(request:Request,
                         driver_uuid = Depends(driver_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
    ):
    attributes = [
        "name",
        "profile_image",
        "years_of_experience",
        "country_code",
        "phone_number",
        "city",
        "pincode",
        "used_ev_before",
        "distance_driven",
        "score",
        "assignments_completed",
        "verification_status",
        "main_profile_completion_percentage",
        "docs_completion_percentage"
    ]

    unique_attribute = {'driver_uuid' : driver_uuid , "is_enable" : True}
    
    data = await fetch_from_table(session , DriverMain , attributes , unique_attribute)
    data = data[0]
    if data['years_of_experience']:
        current_date = get_utc_time()
        delta = current_date - data['years_of_experience']

        years_of_experience = round(delta.days / 365.25, 2)
        data['years_of_experience'] = years_of_experience
    
    mapping_instance = await get_tuple_instance(
        session ,
        DriverMfoMapping ,
        {"driver_uuid" : driver_uuid , "is_enable" : True},
        order_by=[desc(DriverMfoMapping.id)],
        limit = 1)
    if not mapping_instance:
        data['mfo_name'] = None
        data['mfo_country_code'] = None
        data['mfo_phone_number'] = None
        data['business_name'] = None
        data['business_logo'] = None
    else:
        mfo_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : mapping_instance.mfo_uuid , "is_enable" : True})
        mfo_business_instance = await get_tuple_instance(session , MfoBusiness , {"mfo_uuid" : mapping_instance.mfo_uuid})
        data['mfo_name'] = mfo_instance.name
        data['mfo_country_code'] = mfo_instance.country_code
        data['mfo_phone_number'] = mfo_instance.phone_number
        data['business_name'] = mfo_business_instance.business_name
        data['business_logo'] = mfo_business_instance.logo
    await session.commit()
    await session.close()
    return success_response(request , get_profile_data_response(**data) , message = "Profile Data Fetched successfully")




@driver_get_basic_data_router.get("/getDocsData" , response_model = standard_success_response[get_docs_data_response] , status_code=200)
async def getDocsData(request:Request,
                      driver_uuid = Depends(driver_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
    ):

    attributes = list(get_docs_data_response.model_fields.keys()) 
    unique_attribute = {'driver_uuid' : driver_uuid , "is_enable" : True}
    
    data = await fetch_from_table(session , DriverMain , attributes , unique_attribute)
    data = data[0]
    await session.commit()
    await session.close()
    return success_response(request , get_docs_data_response(**data) , message = "Docs Data Fetched successfully")






# @driver_get_basic_data_router.get("/getVehicleData" , response_model = standard_success_response[get_vehicle_data_response] , status_code=200)
# async def getVehicleData(request:Request,
#                          driver_uuid = Depends(driver_role_required()),
#                         session:AsyncSession = Depends(get_async_db),
#                         session_id: str = Header(..., alias="session-id"),
#                         device_id: str = Header(..., alias="device-id")
#     ):
#     async with session.begin():
#         query1 = select(VehicleMain.vehicle_number,
#                         VehicleMain.vehicle_uuid,
#                         DriverVehicleMapping.driver_role
#                         ).join(
#                             DriverVehicleMapping , VehicleMain.vehicle_uuid == DriverVehicleMapping.vehicle_uuid
#                         ).where(
#                             DriverVehicleMapping.driver_uuid == driver_uuid
#                         )
        
#         query2 = select(
#             VehicleMain.vehicle_number,
#             VehicleMain.vehicle_uuid,
#             VehicleMain.bluetooth_id,
#             VehicleMain.bluetooth_connection_status
#         ).join(
#             MfoVehicleMapping , VehicleMain.vehicle_uuid == MfoVehicleMapping.vehicle_uuid
#         ).where(
#             MfoVehicleMapping.current_assigned_driver == driver_uuid
#         )
        
        
#         result1 = await session.execute(query1)
#         vehicle_data = result1.fetchall()
#         vehicle_driver_list = [
#             {"vehicle_uuid" : row.vehicle_uuid , "vehicle_number": row.vehicle_number, "role": row.driver_role}
#             for row in vehicle_data
#         ]
#         if vehicle_driver_list:
#             driver_roles_dict = static_table_settings.static_table_data['DRIVER_ROLES']
#             for veh in vehicle_driver_list:
#                 veh['role'] = driver_roles_dict[veh['role']]
                
                
        
#         result2 = await session.execute(query2)
#         current_vehicle_data = result2.fetchall()
#         present_status = False
#         if not current_vehicle_data:
#             vehicle_current_assigned_dict = {"current_assigned_details": {}}

#         elif len(current_vehicle_data) > 1:
#             raise InvalidRequestError("Multiple vehicles assigned to the driver. Data inconsistency detected."
#             )

#         else:
#             attendance = await get_tuple_instance(
#                     session,
#                     DriverAttendance,
#                     {'driver_uuid': driver_uuid},
#                     extra_conditions=[
#                         func.DATE(convert_utc_to_ist(DriverAttendance.attendance_trigger_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
#                     ],
#                     order_by=[desc(DriverAttendance.attendance_trigger_time)],
#                     limit=1  
#                 )
#             attendance_status_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
#             present_marked_uuid = next((k for k, v in attendance_status_dict.items() if v == 'Present'), None)
#             if attendance and attendance.attendance_state_uuid == present_marked_uuid:
#                 present_status = True 
#             row = current_vehicle_data[0]
#             vehicle_current_assigned_dict = {
#                 "current_assigned_details": {
#                     "vehicle_uuid": row.vehicle_uuid,
#                     "vehicle_number": row.vehicle_number,
#                     "bluetooth_id": row.bluetooth_id,
#                     "bluetooth_connection_status": row.bluetooth_connection_status,
#                     "vehicle_location": "Iconic Corenthum, Noida Electronic City",
#                 }
#             }
    
#         await session.commit()
    
#     data_res =  get_vehicle_data_response(
#         vehicle_data = vehicle_driver_list,
#         current_assigned_vehicle_details = vehicle_current_assigned_dict['current_assigned_details'],
#         present_status = present_status
#     )
#     return success_response(request , data_res , message = "Vehicle Data Fetched successfully")
    





        

@driver_get_basic_data_router.get("/SOS" , response_model= standard_success_response[SOS_response])
async def SOS(request:Request,
              driver_uuid = Depends(driver_role_required()),
                session:AsyncSession = Depends(get_async_db),
                session_id: str = Header(..., alias="session-id"),
                device_id: str = Header(..., alias="device-id")
                ):

    mapping_instance = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : driver_uuid , "is_enable" : True})
    if not mapping_instance:
        raise NotFoundError("You are not current assigned driver of any MFO")
    
    mfo_main_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : mapping_instance.mfo_uuid , "is_enable" : True})
    if not mfo_main_instance:
        raise NotFoundError("You are not current assigned driver of any MFO")
    
    sos_res = SOS_response(
        mfo_phone_number=mfo_main_instance.phone_number
    )
            
    await session.close()
    return success_response(request , sos_res , message = "Mfo contact number Fetched successfully on SOS")







        

@driver_get_basic_data_router.post("/pushNotification" , response_model= standard_success_response[pushNotification_response])
async def pushNotification_api(request:Request,
                               req:pushNotification_request,
                                driver_uuid = Depends(driver_role_required()),
                                session:AsyncSession = Depends(get_async_db),
                                session_id: str = Header(..., alias="session-id"),
                                device_id: str = Header(..., alias="device-id")
                                ):

    data = {
        "driver_uuid" : driver_uuid,
        "notification_data" : req.notification_data
    }
    await insert_into_table(session , NotificationListner , data)
            
    await session.commit()
    await session.close()
    data_res = pushNotification_response()
    return success_response(request , data_res , message = "notification logged successfully")