from calendar import monthrange
from datetime import datetime, timedelta
from fastapi import APIRouter, BackgroundTasks , Request, Depends , Header
from sqlalchemy import desc
from auth.dependencies import driver_role_required
from config.exceptions import ForbiddenError, NotFoundError
from config.firebase_config import send_fcm_notification
from db.database_operations import fetch_from_table, get_tuple_instance, insert_into_table
from models.assignment_mapping_models import DriverMfoMapping, MfoVehicleMapping
from models.attendace_models import DriverWorkingPolicy, DriverAttendance, DriverAttendanceSummary, DriverLeaveRequest, DriverOffDayWorkRequest
from models.driver_models import DriverMain
from models.mfo_models import MfoMain
from schemas.v1.driver_schemas.attendance_and_leave_management_schema import (
    RequestLeaveRequest,
    RequestLeaveResponse, RequestWorkOnOffDayRequest, 
    RequestWorkOnOffDayResponse,
    getMonthlyCalendarEventsRequest, getMonthlyCalendarEventsRespoonse,
    MonthlySummary , Activity
)
from schemas.v1.standard_schema import standard_success_response
from utils.leave_management_utils import get_off_days
from utils.response import  success_response
from sqlalchemy.ext.asyncio import AsyncSession
from settings.static_data_settings import static_table_settings
from db.db import get_async_db
from utils.time_utils import get_utc_time 



driver_leave_management_router = APIRouter()




@driver_leave_management_router.get("/getMonthlyCalendarEvents" , response_model = standard_success_response[getMonthlyCalendarEventsRespoonse] , status_code=200)
async def getMonthlyCalendarEventsApi(request:Request,
                                   req:getMonthlyCalendarEventsRequest,
                                   driver_uuid = Depends(driver_role_required()),
                                   session:AsyncSession = Depends(get_async_db),
                                   session_id: str = Header(..., alias="session-id"),
                                   device_id: str = Header(..., alias="device-id")
                                   ):
    """
    Retrieve the current month's leave details for a driver.

    Args:
        request (Request): FastAPI request object.
        driver_uuid (str): UUID of the authenticated driver (from token).
        session (AsyncSession): Database session.
        session_id (str): Session ID from request headers.
        device_id (str): Device ID from request headers.

    Returns:
        standard_success_response[getMonthlyCalendarEventsRespoonse]: API response containing Monthly leave and request on work details.
    """
    mapping_instance = await get_tuple_instance(session , DriverMfoMapping , {"driver_uuid" : driver_uuid , "is_enable" : True} , order_by = [desc(DriverMfoMapping.id)],limit = 1)
    if not mapping_instance:
        raise NotFoundError("Not working with any MFO")
    current_assigned_vehicle_instance = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : driver_uuid , "is_enable" : True})
    monthly_calendar_events = {}
    monthly_off_days = []
    if current_assigned_vehicle_instance:
        driver_policy_instance = await get_tuple_instance(session , DriverWorkingPolicy , {"driver_uuid" : driver_uuid , "mfo_uuid" : current_assigned_vehicle_instance.mfo_uuid , "valid_till" : None} , order_by=[desc(DriverWorkingPolicy.id)] , limit = 1)
        driver_policy_uuid = driver_policy_instance.driver_policy_uuid
        monthly_off_days = await get_off_days(session , driver_policy_uuid , req.year , req.month)
        for days in monthly_off_days:
            monthly_calendar_events[days] = (Activity( event = "Off day"))
    
    
    start_date = datetime(req.year, req.month, 1)
    _, last_day = monthrange(req.year, req.month)
    end_date = datetime(req.year, req.month, last_day , 23 , 59)
    
    
    present_count = 0
    leave_counts = 0
    overtime_counts = 0
    final_achieved_days = 0
    monthly_working_days = last_day - len(monthly_off_days)
    monthly_attendance_summary = await get_tuple_instance(session , DriverAttendanceSummary , {"driver_uuid" : driver_uuid , "year" : req.year , "month" : req.month})
    if monthly_attendance_summary:
        present_count = monthly_attendance_summary.total_present_days
        leave_counts = monthly_attendance_summary.total_leave_days
        overtime_counts = monthly_attendance_summary.total_worked_on_leave_days
        final_achieved_days = monthly_attendance_summary.required_working_days
        monthly_working_days = monthly_attendance_summary.required_working_days
        
    monthly_summary = MonthlySummary(leaves = leave_counts , overtimes= overtime_counts , presents=present_count , final_achieved_days = final_achieved_days , monthly_working_days = monthly_working_days)
        
        
        
        
        
    
    
    
    monthly_activities = {}
    leaves = await fetch_from_table(
        session,
        DriverLeaveRequest,
        columns=["id" , "start_date", "end_date" , "leave_type_uuid" ,"reason" , "leave_status_uuid" , "requested_at" , "reviewed_by"],
        filters=[
            DriverLeaveRequest.driver_uuid == driver_uuid,
            DriverLeaveRequest.start_date >= start_date,
            DriverLeaveRequest.start_date <= end_date
        ],
        order_by="id"
    )
    leave_types_dict = static_table_settings.static_table_data['LEAVE_TYPES']
    
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    
    for leave in leaves:
        leave["leave_type"] = leave_types_dict[leave["leave_type_uuid"]]
        leave["leave_status"] = request_status_dict[leave["leave_status_uuid"]]
        if leave['leave_status'] == "Approved":
            leave_counts+=1
            
        monthly_activities[leave["start_date"].day] = (Activity(event = "leave request" , event_status = leave["leave_status"]))
        
        current_date = leave["start_date"]
        while current_date <= leave["end_date"]:
            monthly_calendar_events[current_date.day] = (Activity( event = "leave request" , event_status=leave['leave_status']))
            current_date += timedelta(days=1)
            
            


    
    work_requests = await fetch_from_table(
        session,
        DriverOffDayWorkRequest,
        columns=["id" , "off_date", "reason" , "request_status_uuid" , "requested_at" , "reviewed_by"],
        filters=[
            DriverOffDayWorkRequest.driver_uuid == driver_uuid,
            DriverOffDayWorkRequest.off_date >= start_date,
            DriverOffDayWorkRequest.off_date <= end_date
        ],
        order_by = "id"
    )
    
    for work_req in work_requests:
        work_req["request_status"] = request_status_dict[work_req["request_status_uuid"]]
        monthly_activities[work_req["off_date"].day] = (Activity(event = "overtime request" , event_status = work_req["request_status"]))
        monthly_calendar_events[work_req["off_date"].day] = (Activity(event = "overtime request" , event_status = work_req["request_status"]))
        
        
        
    attendance_data = await fetch_from_table(
        session , 
        DriverAttendance,
        columns= None,
        filters = [
            DriverAttendance.driver_uuid == driver_uuid,
            DriverAttendance.attendance_trigger_time >= start_date,
            DriverAttendance.attendance_trigger_time <= end_date
        ],
        order_by = "id"
    )
    attendance_states_dict = static_table_settings.static_table_data["ATTENDANCE_STATES"] 
    for attendance in attendance_data:
        if attendance_states_dict[attendance["attendance_state_uuid"]] == "Present" :
            if  attendance["extra_day_work"]:
                monthly_calendar_events[work_req["off_date"].day] = (Activity(event = "overtime worked"))
            else:
                monthly_calendar_events[attendance["attendance_trigger_time"].day] = (Activity(event = "Present"))
        
        
    
    monthly_activities = dict(sorted(monthly_activities.items() , reverse=True))
    
    data_res = getMonthlyCalendarEventsRespoonse(
        monthly_calendar_events = monthly_calendar_events,
        monthly_summary= monthly_summary,
        monthly_activities=monthly_activities
    )
    await session.commit()
    await session.close()

    return success_response(request, data_res, message="Data fetched successfully")










@driver_leave_management_router.post("/requestLeave" , response_model = standard_success_response[RequestLeaveResponse] , status_code=201)
async def requestLeave(req:RequestLeaveRequest,
                       background_tasks:BackgroundTasks,
                       request:Request,
                       driver_uuid = Depends(driver_role_required()),
                       session:AsyncSession = Depends(get_async_db),
                       session_id: str = Header(..., alias="session-id"),
                       device_id: str = Header(..., alias="device-id"),
                       ):
    """
    Submit a leave request for the authenticated driver.

    This endpoint allows a driver to request a leave for a specific date or date range,
    with optional reasons and leave type (e.g., paid/unpaid).

    Args:
        req (RequestLeaveRequest): The request body containing leave details.
        request (Request): FastAPI request object for metadata.
        driver_uuid (str): UUID of the authenticated driver extracted from the token.
        session (AsyncSession): Database session dependency.
        session_id (str): Unique session ID passed via request header.
        device_id (str): Unique device ID passed via request header.

    Returns:
        standard_success_response[RequestLeaveResponse]: 
            A response indicating the leave request has been processed successfully.
    """
    
    today = get_utc_time().date()
    start_date = req.start_date
    end_date = req.end_date
    
    
    if (start_date - today).days < 3:
        raise ForbiddenError("Leave start date must be at least 3 days from today.")

    if start_date > end_date:
        raise ForbiddenError("Leave start date cannot be after end date.")
    
    if (end_date - start_date).days > 4:
        raise ForbiddenError("Can't request leave for more than 4 days")
    
    leave_types_dict = static_table_settings.static_table_data['LEAVE_TYPES']
    sick_leave_uuid = next((k for k, v in leave_types_dict.items() if v == req.leave_type), None)
    
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    pending_request_uuid = next((k for k, v in request_status_dict.items() if v == 'Pending'), None)
    
    mfo_vehicle_instance = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : driver_uuid , "is_enable" : True})
    leave_request_dict = {
        "driver_uuid": driver_uuid,
        "mfo_uuid" : mfo_vehicle_instance.mfo_uuid,
        "start_date" : req.start_date,
        "end_date" : req.end_date,
        "leave_type_uuid" :  sick_leave_uuid,
        "reason" : req.reason,
        "leave_status_uuid" : pending_request_uuid
    }
    
    
    await insert_into_table(session , DriverLeaveRequest , leave_request_dict)

    response_dict = {
        "start_date" : start_date,
        "end_date" : end_date,
        "leave_type" :  req.leave_type,
        "reason" : req.reason,
    }
    
    data_res = RequestLeaveResponse(**response_dict)
    
    mfo_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : mfo_vehicle_instance.mfo_uuid , "is_enable" : True})
    title = "Review Required: Driver Leave Request"
    message = f"A Driver has requested for Leave from  {start_date} to {end_date}. Please review and take action."
    if start_date == end_date:
        message = f"A Driver has requested on {start_date} . Please review and take action."
    background_tasks.add_task(send_fcm_notification, mfo_instance.fcm_token ,title , message)
    
    await session.commit()
    await session.close()

    return success_response(request ,data_res , message = "Leave requested successfully")








@driver_leave_management_router.post("/requestWorkOnOffDay" , response_model = standard_success_response[RequestWorkOnOffDayResponse] , status_code=201)
async def requestWorkOnLeave(req:RequestWorkOnOffDayRequest,
                             background_tasks: BackgroundTasks,
                             request:Request,
                             driver_uuid = Depends(driver_role_required()),
                             session:AsyncSession = Depends(get_async_db),
                             session_id: str = Header(..., alias="session-id"),
                             device_id: str = Header(..., alias="device-id"),
                             ):
    
    """
    Request to work on leave days.

    This endpoint allows a driver to create request to 
    work on leave days.

    Args:
        req (RequestWorkOnLeaveRequest): The request body containing work on leave request details.
        request (Request): FastAPI request object for metadata.
        driver_uuid (str): UUID of the authenticated driver extracted from the token.
        session (AsyncSession): Database session dependency.
        session_id (str): Unique session ID passed via request header.
        device_id (str): Unique device ID passed via request header.

    Returns:
        standard_success_response[RequestWorkOnLeaveRequest]: 
            A response with acknowledgement of request created for work on leave day.
    """
    today = get_utc_time().date()
    working_date = req.working_date

    if working_date <= today:
        raise ForbiddenError("Working request must be at least 1 days from working day.")
    
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    pending_request_uuid = next((k for k, v in request_status_dict.items() if v == 'Pending'), None)
    mfo_vehicle_instance = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : driver_uuid , "is_enable" : True})
    working_request_dict = {
        "driver_uuid": driver_uuid,
        "mfo_uuid" : mfo_vehicle_instance.mfo_uuid,
        "off_date" : working_date,
        "reason" : req.reason,
        "request_status_uuid" : pending_request_uuid
    }
    
    already_requested = await get_tuple_instance(session ,
                                                 DriverOffDayWorkRequest ,
                                                 {"driver_uuid" : driver_uuid , 
                                                  "mfo_uuid" : mfo_vehicle_instance.mfo_uuid,
                                                  "off_date" : working_date
                                                  },
                                                 order_by= [desc(DriverOffDayWorkRequest.id)],
                                                 limit = 1)
    if already_requested:
        if already_requested.request_status_uuid == pending_request_uuid:
            raise ForbiddenError("You already have a same pending work request")
        
    await insert_into_table(session , DriverOffDayWorkRequest , working_request_dict)
    
    response_dict = {
        "working_date" : req.working_date,
        "reason" : req.reason,
    }
    data_res = RequestWorkOnOffDayResponse(**response_dict)
    
    mfo_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : mfo_vehicle_instance.mfo_uuid , "is_enable" : True})
    title = "Review Required: Driver Extra Work Request"
    message = f"A Driver has requested extra work on  {working_date} . Please review and take action."
    background_tasks.add_task(send_fcm_notification, mfo_instance.fcm_token ,title , message)
    
    await session.commit()
    await session.close()

    return success_response(request ,data_res , message = "Work on leave requested successfully")


