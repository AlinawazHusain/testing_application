from typing import Any
from fastapi import APIRouter , Depends, Header, Request
from auth.jwt import create_access_token, create_refresh_token, verify_token
from auth.otp_service import send_otp, verify_otp
from models.driver_models import DriverMain
from schemas.v1.standard_schema import standard_success_response
from schemas.v1.driver_schemas.driver_onboarding_schema import (
    driver_refresh_access_token_request, driver_refresh_access_token_response,
    driver_send_otp_request, driver_send_otp_response, driver_verify_otp_request,
    driver_verify_otp_response 
    )

from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from db.db import get_async_db
from db.database_operations import  get_tuple_instance, insert_into_table
from utils.response import success_response
from utils.time_utils import get_utc_time

driver_onboarding_router = APIRouter()



@driver_onboarding_router.post("/sendOtp" , response_model = standard_success_response[driver_send_otp_response] , status_code=200)
async def send_otp_api(request:Request,
                        req: driver_send_otp_request,
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")):
    request_id:str =  await send_otp(req.country_code , req.phone_number)
    response =  driver_send_otp_response(
            request_id = request_id
        )
    return success_response(request ,data = response , message = "OTP send successfully")



@driver_onboarding_router.post("/verifyOtp", response_model= standard_success_response[driver_verify_otp_response], status_code=201)
async def verify_otp_api(request:Request,
                          req: driver_verify_otp_request,
                          session: AsyncSession = Depends(get_async_db),
                          session_id: str = Header(..., alias="session-id"),
                          device_id: str = Header(..., alias="device-id")
                          ):
    playstore_phone_number = "9760410914"
    if req.phone_number != playstore_phone_number:
        await verify_otp(req.otp, req.request_id)
        
    driver_already_exist = False

    async with session.begin():
        driver_instance = await get_tuple_instance(session , DriverMain , {"phone_number" :  req.phone_number , "is_enable" : True})
        
        if driver_instance:
            driver_instance.fcm_token[req.device_id ] =  req.fcm_token
            driver_already_exist = True
            driver_uuid = driver_instance.driver_uuid
            driver_instance.device_id = req.device_id
            driver_instance.ip_address = req.ip_address
            driver_instance.device_model = req.device_model
            driver_instance.device_language = req.device_language
            driver_instance.device_brand = req.device_brand
            driver_instance.support_nfc = req.support_nfc
        else:
            new_driver_data = {
                'country_code' : req.country_code,
                'phone_number' : req.phone_number,
                'fcm_token'  : {req.device_id : req.fcm_token},
                'device_id' : req.device_id,
                'ip_address' : req.ip_address,
                'device_model' : req.device_model,
                'device_language' : req.device_language,
                'device_brand' : req.device_brand,
                'support_nfc' : req.support_nfc
            }
            
            created_driver = await insert_into_table(session , DriverMain , new_driver_data)
            driver_uuid = created_driver.driver_uuid

        await session.commit()

    jwt_data = {"driver_uuid": driver_uuid, "role": "driver"}
    
    tokens: tuple[str, str] = await asyncio.gather(
    create_access_token(data = jwt_data),
    create_refresh_token(data = jwt_data)
    )

    access_token, refresh_token  = tokens

    response =  driver_verify_otp_response(
        driver_uuid = driver_uuid,
        exists =  driver_already_exist,
        access_token = access_token,
        refresh_token = refresh_token,
        token_type =  "bearer"
    )
    return success_response(request , data = response , message = "OTP verified successfully")



@driver_onboarding_router.get("/refreshAccessToken" , response_model = standard_success_response[driver_refresh_access_token_response] , status_code = 200)
async def refresh_access_token_api(request:Request,
                               req: driver_refresh_access_token_request,
                               session_id: str = Header(..., alias="session-id"),
                               device_id: str = Header(..., alias="device-id")
                               ):
        """
        Takes a refresh token and returns a new access token.
        """
        payload:dict[str , Any] = await verify_token(token = req.refresh_token)
        new_access_token:str = await create_access_token(data = payload)
        response =  driver_refresh_access_token_response(
            access_token = new_access_token,
            token_type =  'bearer'
        )
        return success_response(request , data = response , message = "New access token created successfully")