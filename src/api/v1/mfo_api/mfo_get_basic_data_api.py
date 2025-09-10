from fastapi import APIRouter, Depends, Header, Request
from auth.dependencies import mfo_role_required
from db.database_operations import fetch_from_table
from models.mfo_models import MfoBusiness, MfoMain, MfoVehicleLeasing
from schemas.v1.standard_schema import standard_success_response
from schemas.v1.mfo_schemas.mfo_get_basic_data_schema import (
    get_business_data_response, get_business_docs_response,
    get_leasing_docs_response, get_profile_data_response
    )
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from utils.response import success_response





mfo_get_basic_data_router = APIRouter()










@mfo_get_basic_data_router.get("/getProfileData" , response_model= standard_success_response[get_profile_data_response] , status_code=200)
async def getProfileData(request:Request,
                         mfo_uuid= Depends(mfo_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    attributes = list(get_profile_data_response.model_fields.keys()) 
    unique_attribute = {'mfo_uuid' : mfo_uuid , "is_enable" : True}
    data = await fetch_from_table(session , MfoMain , attributes , unique_attribute)
    data = data[0]
    await session.commit()
    await session.close()
    data_res = get_profile_data_response(**data)
    return success_response(request , data_res , message = "Profile Data Get successfully")



@mfo_get_basic_data_router.get("/getBusinessData" , response_model= standard_success_response[get_business_data_response] , status_code=200)
async def getBusinessData(request:Request,
                          mfo_uuid= Depends(mfo_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    attributes = list(get_business_data_response.model_fields.keys()) 
    attributes.remove("leasing_docs_completion_percentage")
    unique_attribute = {'mfo_uuid' : mfo_uuid}
    data = await fetch_from_table(session , MfoBusiness , attributes , unique_attribute)
    data = data[0]
    leasing_docs_complete_percentage = await fetch_from_table(session , MfoVehicleLeasing , ['leasing_docs_completion_percentage'] , unique_attribute)
    leasing_docs_complete_percentage = leasing_docs_complete_percentage[0]['leasing_docs_completion_percentage']
    data['leasing_docs_completion_percentage'] = leasing_docs_complete_percentage
    await session.commit()
    await session.close()
    data_res = get_business_data_response(**data)
    return success_response(request , data_res , message = "Business Data Get successfully")
        
        
        
        
@mfo_get_basic_data_router.get("/getBusinessDocs" , response_model=standard_success_response[get_business_docs_response], status_code=200)
async def getLeasingData(request:Request,
                         mfo_uuid= Depends(mfo_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    attributes = list(get_business_docs_response.model_fields.keys()) 
    unique_attribute = {'mfo_uuid' : mfo_uuid}
    data = await fetch_from_table(session , MfoBusiness , attributes , unique_attribute)
    data = data[0]
    await session.commit()
    await session.close()
    data_res = get_business_docs_response(**data)
    return success_response(request , data_res , message = "Business Docs Get successfully")

        


@mfo_get_basic_data_router.get("/getLeasingDocs" , response_model= standard_success_response[get_leasing_docs_response] , status_code=200)
async def getLeasingData(request:Request,
                         mfo_uuid= Depends(mfo_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    attributes = None
    unique_attribute = {'mfo_uuid' : mfo_uuid}
    data = await fetch_from_table(session , MfoVehicleLeasing , attributes , unique_attribute)
    data = data[0]
    await session.commit()
    await session.close()
    data_res = get_leasing_docs_response(**data)
    return success_response(request , data_res , message = "Leasing Docs Get successfully")

