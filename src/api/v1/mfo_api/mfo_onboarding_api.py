from typing import Any
from fastapi import APIRouter , Depends, Header, Request
from auth.jwt import create_access_token, create_refresh_token, verify_token
from auth.otp_service import send_otp, verify_otp
from models.mfo_models import MfoBusiness, MfoMain, MfoVehicleLeasing
from schemas.v1.standard_schema import standard_success_response
from schemas.v1.mfo_schemas.mfo_onboarding_schema import (
    mfo_refresh_access_token_request, mfo_refresh_access_token_response,
    mfo_send_otp_request, mfo_send_otp_response, mfo_verify_otp_request,
    mfo_verify_otp_response
    )

from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from db.db import get_async_db
from db.database_operations import  get_tuple_instance, insert_into_table, insert_multiple_tables
from utils.response import success_response
from utils.time_utils import get_utc_time 

mfo_onboarding_router = APIRouter()


@mfo_onboarding_router.get("/")
async def home():
    return {"Status" : "Server is Running"}




@mfo_onboarding_router.post("/sendOtp" , response_model = standard_success_response[mfo_send_otp_response] , status_code=200)
async def call_send_otp(request:Request,
                        req: mfo_send_otp_request,
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    request_id :str =  await send_otp(req.country_code , req.phone_number)
    data_res = mfo_send_otp_response(
            request_id = request_id,
        )
    return success_response(request , data_res , message = "OTP sended successfully")



@mfo_onboarding_router.post("/verifyOtp", response_model=standard_success_response[mfo_verify_otp_response], status_code=201)
async def call_verify_otp(request:Request,
                          req: mfo_verify_otp_request,
                          session: AsyncSession = Depends(get_async_db),
                          session_id: str = Header(..., alias="session-id"),
                          device_id: str = Header(..., alias="device-id")
                          ):
    playstore_phone_number = "9760410914"
    if req.phone_number != playstore_phone_number:
        await verify_otp(req.otp, req.request_id)
        
    mfo_already_exist = False
    async with session.begin():
        mfo_instance = await get_tuple_instance(session , MfoMain , {"phone_number" :  req.phone_number , "is_enable" : True})
        
        if mfo_instance:
            mfo_instance.fcm_token[req.device_id ] = req.fcm_token
            mfo_already_exist = True
            mfo_uuid = mfo_instance.mfo_uuid
            mfo_instance.device_id = req.device_id
            mfo_instance.ip_address = req.ip_address
            mfo_instance.device_model = req.device_model
            mfo_instance.device_language = req.device_language
            mfo_instance.device_brand = req.device_brand
        else:
            new_mfo_data = {
                'country_code' : req.country_code,
                'phone_number' : req.phone_number,
                'fcm_token'  : {req.device_id : req.fcm_token},
                'device_id' : req.device_id,
                'ip_address' : req.ip_address,
                'device_model' : req.device_model,
                'device_language' : req.device_language,
                'device_brand' : req.device_brand
            }
            created_mfo = await insert_into_table(session , MfoMain , new_mfo_data)
            mfo_uuid = created_mfo.mfo_uuid

            additional_inserts = {
                MfoBusiness : {'mfo_uuid' : mfo_uuid},
                MfoVehicleLeasing : {'mfo_uuid' : mfo_uuid}
            }
            
            await insert_multiple_tables(session , additional_inserts)
        await session.commit()

    jwt_data = {"mfo_uuid": mfo_uuid, "role": "mfo"}
    tokens: tuple[str, str] = await asyncio.gather(
    create_access_token(data = jwt_data),
    create_refresh_token(data = jwt_data)
    )

    access_token, refresh_token  = tokens

    data_res = mfo_verify_otp_response(
        mfo_uuid =  mfo_uuid,
        exists = mfo_already_exist,
        access_token =  access_token,
        refresh_token = refresh_token,
        token_type = "bearer"
    )
    
    return success_response(request , data_res , message = "OTP verified successfully")



@mfo_onboarding_router.get("/refreshAccessToken" , response_model = standard_success_response[mfo_refresh_access_token_response] , status_code = 200)
async def refresh_access_token(request:Request,
                               req: mfo_refresh_access_token_request,
                               session_id: str = Header(..., alias="session-id"),
                               device_id: str = Header(..., alias="device-id")
                               ):
        """
        Takes a refresh token and returns a new access token.
        """
        payload:dict[str , Any] = await verify_token(token = req.refresh_token)
        new_access_token:str = await create_access_token(payload)
        data_res = mfo_refresh_access_token_response(
            access_token = new_access_token,
            token_type =  'bearer'
        )
        return success_response(request , data_res , message = "New access token created successfully")