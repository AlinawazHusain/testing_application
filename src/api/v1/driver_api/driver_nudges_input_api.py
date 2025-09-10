from fastapi import APIRouter , Depends, Header, Request 
from auth.dependencies import driver_role_required
from config.exceptions import NotFoundError
from db.database_operations import insert_into_table
from models.log_models import DriverNudgesResponses
from models.task_management_models import Tasks
from schemas.v1.driver_schemas.driver_nudges_input_schema import send_nudge_response_request, send_nudge_response_response
from schemas.v1.standard_schema import standard_success_response
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from utils.response import success_response



driver_nudges_input_router = APIRouter()




@driver_nudges_input_router.post("/sendNudgeResponse" , response_model= standard_success_response[send_nudge_response_response] , status_code = 200)
async def sendNudgeResponse(request:Request,
                            req: send_nudge_response_request,
                            driver_uuid = Depends(driver_role_required()),
                            session:AsyncSession = Depends(get_async_db),
                            session_id: str = Header(..., alias="session-id"),
                            device_id: str = Header(..., alias="device-id")
                            ):
    nudge_data = {
        "driver_uuid" : driver_uuid,
        "nudge_response"  : req.nudge_response,
        "action_type" :req.action_type,
        "overlay_text" : req.overlay_text
    }
    await insert_into_table(session , DriverNudgesResponses , nudge_data)
    await session.commit()
    await session.close()
    data_res = send_nudge_response_response()
    return success_response(request , data_res , "nudge response saved successfully")