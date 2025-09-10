from fastapi import APIRouter , Form , File, Header, Request , UploadFile , Depends
from datetime import timedelta
from auth.dependencies import mfo_role_required
from db.database_operations import update_percentage_including, update_table
from integrations.appyflow import get_gst_Address
from integrations.aws_utils import upload_file_to_s3
from models.mfo_models import MfoBusiness, MfoMain, MfoVehicleLeasing
from schemas.v1.standard_schema import standard_success_response
from schemas.v1.mfo_schemas.mfo_account_management_schema import (
    create_profile_request, create_profile_response, delete_account,
    mfo_update_business_attributes_request, mfo_update_business_attributes_response,
    mfo_update_business_file_response, mfo_update_business_file_valid_attributes,
    mfo_update_leasing_file_response, mfo_update_leasing_file_valid_attributes,
    mfo_update_main_attributes_request, mfo_update_main_attributes_response,
    mfo_update_main_file_response, mfo_update_main_file_valid_attributes
)
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from utils.response import success_response
from utils.time_utils import get_utc_time



mfo_account_management_router = APIRouter()






@mfo_account_management_router.put("/createProfile" , response_model = standard_success_response[create_profile_response] , status_code=201)
async def createProfile(request:Request,
                        req : create_profile_request,
                        mfo_uuid = Depends(mfo_role_required()),
                        session: AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                      ):
    
    mfo_main_update_data = {"name" : req.name}
    days_in_year = 365.25
    years = round(req.years_of_experience, 2)
    days_to_subtract = int(years * days_in_year)

    current_date = get_utc_time()
    new_date = current_date - timedelta(days=days_to_subtract)
    mfo_main_update_data['years_of_experience'] = new_date
        
    mfo_business_update_data = {}
    mfo_business_update_data['total_number_of_vehicles'] = req.number_of_vehicles 
    mfo_business_update_data['total_number_of_evs'] = req.number_of_evs
    
    await update_table(session , MfoMain , {"mfo_uuid" : mfo_uuid} , mfo_main_update_data)
    await update_table(session , MfoBusiness , {"mfo_uuid" : mfo_uuid} , mfo_business_update_data)
    
    await session.commit()
    await session.close()
    data_res =  create_profile_response(**req.model_dump())
    return success_response(request , data_res , message = "Profile created successfully")








@mfo_account_management_router.post("/updateMainFile" , response_model = standard_success_response[mfo_update_main_file_response] , status_code=200)
async def updateMainFile(request:Request,
                         file_attribute:mfo_update_main_file_valid_attributes = Form(...),
                         file :UploadFile =  File(...),
                         mfo_uuid = Depends(mfo_role_required()),
                         session: AsyncSession = Depends(get_async_db),
                         session_id: str = Header(..., alias="session-id"),
                         device_id: str = Header(..., alias="device-id")
                         ):
    dt = get_utc_time().strftime("%Y-%m-%d_%H-%M-%S")
    UPLOAD_FOLDER_DRIVER = f"mfo/{mfo_uuid}"

    file_extension = file.filename.split('.')[-1].lower()
    file_path = f"{UPLOAD_FOLDER_DRIVER}/{file_attribute}_{dt}.{file_extension}"
    path_to_s3 = await upload_file_to_s3(file , file_path)  
    update_res = await update_table(session , MfoMain , {'mfo_uuid' : mfo_uuid} , {file_attribute : path_to_s3})
    
    include_attributes = ['phone_number' , 'pincode' , 'name' , 'email' ,  'profile_image' , 'aadhar_card' , 'pan_card' ,'aadhar_card_back' ,  'business_name']
    percentage = await update_percentage_including(session , MfoMain , {'mfo_uuid' : mfo_uuid}, include_attributes , 'profile_completion_percentage')
    update_res['profile_completion_percentage'] = percentage
    
    await session.commit()
    await session.close()
    data_res =  mfo_update_main_file_response(
        file_path = path_to_s3,
        main_profile_completion_percentage = percentage
    )
    
    return success_response(request , data_res , message = "File Updated successfully")
    


@mfo_account_management_router.post("/updateBusinessFile" , response_model = standard_success_response[mfo_update_business_file_response] , status_code=200)
async def updateBusinessFile(request:Request,
                            file_attribute:mfo_update_business_file_valid_attributes = Form(...),
                            file :UploadFile =  File(...),
                            mfo_uuid = Depends(mfo_role_required()),
                            session: AsyncSession = Depends(get_async_db),
                            session_id: str = Header(..., alias="session-id"),
                            device_id: str = Header(..., alias="device-id")
                            ):

    dt = get_utc_time().strftime("%Y-%m-%d_%H-%M-%S")
    UPLOAD_FOLDER_DRIVER = f"mfo/{mfo_uuid}"

    file_extension = file.filename.split('.')[-1].lower()
    file_path = f"{UPLOAD_FOLDER_DRIVER}/{file_attribute}_{dt}.{file_extension}"
    path_to_s3 = await upload_file_to_s3(file , file_path)  
    update_res = await update_table(session , MfoBusiness , {'mfo_uuid' : mfo_uuid} , {file_attribute : path_to_s3})
    
    include_attributes = ['logo' , 'business_pan_card','msme_certificate','gst_certificate','udyam_registration','shop_and_establishment_act_license','partnership_deed','certificate_of_incorporation']
    percentage = await update_percentage_including(session , MfoBusiness , {'mfo_uuid' : mfo_uuid}, include_attributes , 'business_docs_completion_percentage')
    update_res['business_docs_completion_percentage'] = percentage
    await session.commit()
    await session.close()
    data_res = mfo_update_business_file_response(
        file_path = path_to_s3,
        business_docs_completion_percentage = percentage
    )
    return success_response(request , data_res , message = "File Updated successfully")
    
        
        
        

@mfo_account_management_router.post("/updateLeasingFile" , response_model = standard_success_response[mfo_update_leasing_file_response] , status_code=200)
async def updateLeasingFile(request:Request,
                            file_attribute:mfo_update_leasing_file_valid_attributes = Form(...),
                            file :UploadFile =  File(...),
                            mfo_uuid = Depends(mfo_role_required()),
                            session:AsyncSession = Depends(get_async_db),
                            session_id: str = Header(..., alias="session-id"),
                            device_id: str = Header(..., alias="device-id")
                            ):
    dt = get_utc_time().strftime("%Y-%m-%d_%H-%M-%S")
    UPLOAD_FOLDER_DRIVER = f"mfo/{mfo_uuid}"

    file_extension = file.filename.split('.')[-1].lower()
    file_path = f"{UPLOAD_FOLDER_DRIVER}/{file_attribute}_{dt}.{file_extension}"
    path_to_s3 = await upload_file_to_s3(file , file_path)  
    update_res = await update_table(session , MfoVehicleLeasing , {'mfo_uuid' : mfo_uuid} , {file_attribute : path_to_s3})
    include_attributes = ['bank_statement','itr','balance_sheet','proof_of_income_from_logistic_business']
    percentage = await update_percentage_including(session , MfoVehicleLeasing , {'mfo_uuid' : mfo_uuid}, include_attributes , 'leasing_docs_completion_percentage')
    update_res['leasing_docs_completion_percentage'] = percentage
    await session.commit()
    await session.close()
    data_res = mfo_update_leasing_file_response(
        file_path = path_to_s3,
        leasing_docs_completion_percentage = percentage
    )
    return success_response(request , data_res , message = "File Updated successfully")
    













@mfo_account_management_router.put("/updateMainAttribute" , response_model = standard_success_response[mfo_update_main_attributes_response] , status_code=200)
async def updateMainAttribute(request:Request,
                              req : mfo_update_main_attributes_request,
                            mfo_uuid= Depends(mfo_role_required()),
                            session:AsyncSession = Depends(get_async_db),
                            session_id: str = Header(..., alias="session-id"),
                            device_id: str = Header(..., alias="device-id")
                            ):
    unique_attribute = {"mfo_uuid" : mfo_uuid}
    update_attribute_data = req.updates
    
    if 'years_of_experience' in update_attribute_data.keys():
        days_in_year = 365.25
        years = round(update_attribute_data['years_of_experience'], 2)
        days_to_subtract = int(years * days_in_year)

        current_date = get_utc_time()
        new_date = current_date - timedelta(days=days_to_subtract)
        update_attribute_data['years_of_experience'] = new_date
        
    update_res = await update_table(session , MfoMain , unique_attribute , update_attribute_data)
    
    include_attributes = ['phone_number' , 'pincode' , 'name' , 'email' ,  'profile_image' , 'aadhar_card' , 'pan_card' ,'aadhar_card_back' ,  'business_name']
    
    percentage = await update_percentage_including(session , MfoMain , {'mfo_uuid' : mfo_uuid}, include_attributes , 'profile_completion_percentage')
    update_res['profile_completion_percentage'] = percentage
    if update_res.get('years_of_experience' , None):
        current_date = get_utc_time()
        delta = current_date - update_res['years_of_experience']
        years_of_experience = round(delta.days / 365.25, 2)
        update_res['years_of_experience'] = years_of_experience
    
    await session.commit()
    await session.close()
        
    data_res =  mfo_update_main_attributes_response(
        updated_data = update_res
    )
    return success_response(request , data_res , message = "Attributes Updated successfully")





@mfo_account_management_router.put("/updateBusinessAttribute" , response_model = standard_success_response[mfo_update_business_attributes_response] , status_code=200)
async def updateBusinessAttribute(request:Request,
                                  req : mfo_update_business_attributes_request,
                                    mfo_uuid= Depends(mfo_role_required()),
                                    session:AsyncSession = Depends(get_async_db),
                                    session_id: str = Header(..., alias="session-id"),
                                    device_id: str = Header(..., alias="device-id")
                                    ):
    unique_attribute = {"mfo_uuid" : mfo_uuid}
    update_attribute_data = req.updates
    if 'gst_number' in update_attribute_data.keys():
        update_attribute_data['registered_office_address'] = await get_gst_Address(update_attribute_data['gst_number'])
    update_res = await update_table(session , MfoBusiness , unique_attribute , update_attribute_data)
    await session.commit()
    await session.close()
    data_res = mfo_update_business_attributes_response(
        updated_data = update_res
    )
    return success_response(request , data_res , message = "Attributes Updated successfully")


@mfo_account_management_router.put("/deleteAccount" , response_model = standard_success_response[delete_account] , status_code=200)
async def deleteAccount(request:Request,
                        mfo_uuid= Depends(mfo_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    await session.commit()
    await session.close()
    data_res =delete_account(deleted = True)
    return success_response(request , data_res , message = "Account deleted successfully")

