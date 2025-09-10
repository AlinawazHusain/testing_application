from fastapi import APIRouter, Depends, Header, Request
from auth.dependencies import driver_role_required
from config.exceptions import  NotFoundError
from db.database_operations import  get_tuple_instance
from db.db import get_async_db
from models.attendace_models import DriverAttendanceSummary
from models.incentive_models import MonthlyDriverIncentive
from schemas.v1.driver_schemas.driver_dashboard_schemas import getMonthlyOverviewReqeust, getMonthlyOverviewResponse
from schemas.v1.standard_schema import standard_success_response
from sqlalchemy.ext.asyncio import AsyncSession

from utils.response import success_response



driver_dashboard_router = APIRouter()


@driver_dashboard_router.get("/getMonthlyOverview" , response_model= standard_success_response[getMonthlyOverviewResponse])
async def getMonthlyOverview(request:Request,
                             req: getMonthlyOverviewReqeust,
                             driver_uuid = Depends(driver_role_required()),
                             session:AsyncSession = Depends(get_async_db),
                             session_id: str = Header(..., alias="session-id"),
                             device_id: str = Header(..., alias="device-id")
                             ):
    monthly_attendance_summary = await get_tuple_instance(session , DriverAttendanceSummary , {"driver_uuid" : driver_uuid ,"year" : req.year , "month" : req.month})
    
    if not monthly_attendance_summary:
        raise NotFoundError("No record found")
    
    monthly_driver_incentive_instance  = await get_tuple_instance(session , MonthlyDriverIncentive , {"driver_uuid" : driver_uuid ,"year" : req.year , "month" : req.month}) 
    
    total_incentive_earned = 0
    total_incentive = 0
    points_earned = 0
    total_points = 0
    
    if monthly_driver_incentive_instance:
        total_incentive_earned = monthly_driver_incentive_instance.total_incentive_earned
        total_incentive = monthly_driver_incentive_instance.total_incentive
        points_earned = monthly_driver_incentive_instance.points_earned
        total_points = monthly_driver_incentive_instance.total_points
        
        
    
    response = getMonthlyOverviewResponse(
        earned_incentive = int(total_incentive_earned),
        total_incentive = int(total_incentive),
        points_earned = points_earned,
        total_points = total_points,
        working_days = monthly_attendance_summary.required_working_days,
        present_days = monthly_attendance_summary.total_present_days,
        leaves = monthly_attendance_summary.total_leave_days, 
        work_on_off_days = monthly_attendance_summary.total_worked_on_leave_days
    )
    
    
    return success_response(request , response , "Monthly overview fetched successfully")