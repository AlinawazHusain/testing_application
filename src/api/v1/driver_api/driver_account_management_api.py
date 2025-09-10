from fastapi import APIRouter , Form , File, Header, Request,UploadFile , Depends 
from datetime import timedelta
from db.database_operations import get_tuple_instance, update_percentage_including, update_table
from integrations.aws_utils import upload_file_to_s3
from logger.db_logger import driver_db_logger
from models.driver_models import DriverMain
from schemas.v1.standard_schema import standard_success_response
from schemas.v1.driver_schemas.driver_account_manaegment_schema import (
    driver_update_main_file_response, driver_update_main_file_valid_attributes,
    driver_update_main_attributes_request , driver_update_main_attributes_response
)
from auth.dependencies import driver_role_required

from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from utils.response import success_response
from utils.time_utils import get_utc_time

driver_account_management_router = APIRouter()






@driver_account_management_router.post("/updateMainFile" , response_model = standard_success_response[driver_update_main_file_response] , status_code=200)
async def updateMainFile(request:Request,
                         file_attribute:driver_update_main_file_valid_attributes = Form(...),
                         file :UploadFile =  File(...),
                         driver_uuid = Depends(driver_role_required()),
                         session:AsyncSession = Depends(get_async_db),
                         session_id: str = Header(..., alias="session-id"),
                         device_id: str = Header(..., alias="device-id")
                         ):
    
    dt = get_utc_time().strftime("%Y-%m-%d_%H-%M-%S")
    
    UPLOAD_FOLDER_DRIVER = f"driver/{driver_uuid}"
    file_extension = file.filename.split('.')[-1].lower()
    file_path = f"{UPLOAD_FOLDER_DRIVER}/{file_attribute}_{dt}.{file_extension}"
    
    path_to_s3:str = await upload_file_to_s3(file , file_path)
    
    table_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : driver_uuid , "is_enable" : True})
    await driver_db_logger(session , driver_uuid , DriverMain.__tablename__ ,"driver_uuid" , driver_uuid, [file_attribute] , [getattr(table_instance, file_attribute)] , [path_to_s3] , session_id , device_id)
    
    data_res = await update_table(session , DriverMain , {'driver_uuid' : driver_uuid , "is_enable" : True} , {file_attribute : path_to_s3})
    
    if file_attribute == driver_update_main_file_valid_attributes.PROFILE_IMAGE:
        include_attributes = ["name" , "phone_number" , "profile_image" , "pincode" , "years_of_experience" , "used_ev_before" , "alternate_phone_number"]
        percentage = await update_percentage_including(session , DriverMain , {'driver_uuid' : driver_uuid , "is_enable" : True} , include_attributes , 'main_profile_completion_percentage')
        data_res['main_profile_completion_percentage'] = percentage
    
    else:
        include_attributes = ["aadhar_card" , "pan_card" , "driving_license" , "aadhar_card_back"]
        percentage = await update_percentage_including(session , DriverMain , {'driver_uuid' : driver_uuid , "is_enable" : True} , include_attributes , 'docs_completion_percentage')
        data_res['docs_completion_percentage'] = percentage
    await session.commit()
    await session.close()
    response =  driver_update_main_file_response(
        file_attribute = file_attribute,
        file_path = path_to_s3,
        completion_percentage = percentage
    )
    return success_response(request , response , message = "File Updated successfully")
    
    









@driver_account_management_router.put("/updateMainAttribute" , response_model = standard_success_response[driver_update_main_attributes_response] , status_code=200)
async def updateMainAttribute(request:Request,
                              req : driver_update_main_attributes_request ,
                              driver_uuid = Depends(driver_role_required()),
                              session:AsyncSession = Depends(get_async_db),
                              session_id: str = Header(..., alias="session-id"),
                              device_id: str = Header(..., alias="device-id")
                              ):
    update_attribute_data = req.updates
    if 'years_of_experience' in update_attribute_data.keys():
        days_in_year = 365.25
        years = round(update_attribute_data['years_of_experience'], 2)
        days_to_subtract = int(years * days_in_year)

        current_date = get_utc_time()
        new_date = current_date - timedelta(days=days_to_subtract)
        update_attribute_data['distance_driven'] = float(update_attribute_data['years_of_experience'] *12 *2400)
        update_attribute_data['years_of_experience'] = new_date
    
    table_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : driver_uuid , "is_enable" : True})
    await driver_db_logger(session , driver_uuid , DriverMain.__tablename__ ,"driver_uuid" , driver_uuid, list(update_attribute_data.keys()) , [getattr(table_instance, attr) for attr in update_attribute_data.keys()] , list(update_attribute_data.values()) , session_id , device_id)
    
    data_res = await update_table(session , DriverMain , {'driver_uuid' : driver_uuid , "is_enable" : True} , update_attribute_data)
    include_attributes = ["name" , "phone_number" , "profile_image" , "pincode" , "years_of_experience" , "used_ev_before" , "alternate_phone_number"]
    percentage = await update_percentage_including(session , DriverMain , {'driver_uuid' : driver_uuid} , include_attributes , 'main_profile_completion_percentage')
    data_res['main_profile_completion_percentage'] = percentage
    if data_res.get('years_of_experience' , None):
        current_date = get_utc_time()
        delta = current_date - data_res['years_of_experience']
        years_of_experience = round(delta.days / 365.25, 2)
        data_res['years_of_experience'] = years_of_experience
        # data_res['distance_driven'] = float(years_of_experience *12 *2400)
    await session.commit()
    await session.close()
    data_res = driver_update_main_attributes_response(
        updated_data = data_res
    )
    return success_response(request , data_res , message = "Main Attributes Updated successfully")