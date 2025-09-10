from datetime import datetime, timedelta ,time
from fastapi import APIRouter, BackgroundTasks , Request , Depends , Header
from sqlalchemy import desc, func
from config.exceptions import InvalidRequestError, NotFoundError
from config.firebase_config import send_fcm_notification
from db.database_operations import fetch_from_table, get_tuple_instance
from helpers.mfo_helpers.mfo_updates_helper import approve_attendance_request, approve_leave_request, approve_work_request, reject_attendance_request, reject_leave_request, reject_work_request
from models.attendace_models import AttendanceRequests, DriverApprovedLeaves, DriverApprovedOffDayWorks, DriverLeaveRequest, DriverOffDayWorkRequest
from auth.dependencies import mfo_role_required
from models.driver_models import DriverMain
from models.vehicle_models import VehicleMain
from schemas.v1.mfo_schemas.leave_management_schema import (
    ApproveLeaveRequestRequest,
    ApproveLeaveRequestResponse,
    ApproveWorkOnOffDayRequestRequest,
    ApproveWorkOnOffDayRequestResponse,
    DriverLeave,
    DriverWorkOnOffDays,
    GetLeaveRequestsResponse,
    GetWorkOnOffDayRequestsResponse,
    LeaveDetail,
    RejectLeaveRequestRequest,
    RejectLeaveRequestResponse,
    RejectWorkOnOffDayRequestRequest,
    RejectWorkOnOffDayRequestResponse,
    WorkOnOffDaysDetails,
    approve_driver_update_request,
    approve_driver_update_response,
    driver_updates,
    get_driver_updates_response,
    reject_driver_update_request,
    reject_driver_update_response
)
from schemas.v1.standard_schema import standard_success_response
from utils.response import  success_response
from sqlalchemy.ext.asyncio import AsyncSession
from settings.static_data_settings import static_table_settings
from db.db import get_async_db
from utils.time_utils import get_utc_time 




mfo_leave_management_router = APIRouter()






@mfo_leave_management_router.get("/getDriverUpdates" , response_model = standard_success_response[get_driver_updates_response] , status_code=200)
async def getDriverUpdates(request:Request,
                           mfo_uuid = Depends(mfo_role_required()),
                           session:AsyncSession = Depends(get_async_db),
                           session_id: str = Header(..., alias="session-id"),
                           device_id: str = Header(..., alias="device-id")
                           ):
    
    current_day = get_utc_time().date()
    today = datetime.combine(current_day, time.min)
    
    leave_requests = await fetch_from_table(
        session,
        DriverLeaveRequest,
        columns=None,
        filters=[
            DriverLeaveRequest.mfo_uuid == mfo_uuid,
            DriverLeaveRequest.start_date >= today,
        ],
        order_by="-id"
    )
    
    work_requests = await fetch_from_table(
        session,
        DriverOffDayWorkRequest,
        columns=None,
        filters=[
            DriverOffDayWorkRequest.mfo_uuid == mfo_uuid,
            DriverOffDayWorkRequest.off_date >= today,
        ],
        order_by="-id"
    )
    
    atttendance_requests =  await fetch_from_table(
        session,
        AttendanceRequests,
        columns=None,
        filters=[
            AttendanceRequests.mfo_uuid == mfo_uuid,
            func.DATE(AttendanceRequests.created_at) == current_day,
        ],
        order_by="-id"
    )
    
    updates = []
    
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    for row in atttendance_requests:
        driver_uuid = str(row['driver_uuid'])
        start_date = row['created_at']
        end_date = row['created_at']
        request_status = row['attendance_request_status']
        driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : driver_uuid})
        vehicle_instance = await get_tuple_instance(session , VehicleMain , {"mfo_uuid" : mfo_uuid , "driver_uuid" : driver_uuid , "is_enable" : True} , order_by = [desc(VehicleMain.id)] , limit = 1)
        had_action = False
        duration = end_date - start_date
        total_days = int(duration.days) + 1
        days = f"{total_days} day" if total_days == 1 else f"{total_days} days"
        event_status = request_status
        event_text = f"Attendance request"
        if request_status in  ["Approved"  , "Rejected"]:
            had_action = True
            event_text = f"Attendance request {event_status}"
            
        updates.append(
            {
                "event_type" : "attendance request",
                "event_uuid": row['attendance_request_uuid'],
                "driver_name": driver_instance.name,
                "driver_profile_image" : driver_instance.profile_image,
                "driver_uuid": driver_uuid , 
                "driver_country_code" : driver_instance.country_code,
                "driver_phone_number": driver_instance.phone_number,
                "vehicle_uuid" : vehicle_instance.vehicle_uuid if vehicle_instance else "",
                "vehicle_number":vehicle_instance.vehicle_number if vehicle_instance else "",
                "start_date": start_date,
                "end_date":end_date,
                "event_status":event_status,
                "event_text" : event_text,
                "had_action":had_action,
                "update_timestamp" : row['created_at']
            }
        )
        
    
    for row in leave_requests:
        driver_uuid = str(row['driver_uuid'])
        leave_request_uuid = row['leave_request_uuid']
        start_date = row['start_date']
        end_date = row['end_date']
        leave_status = request_status_dict[row['leave_status_uuid']]
        driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : driver_uuid})
        vehicle_instance = await get_tuple_instance(session , VehicleMain , {"mfo_uuid" : mfo_uuid , "driver_uuid" : driver_uuid , "is_enable" : True} , order_by = [desc(VehicleMain.id)] , limit = 1)
        had_action = False
        duration = end_date - start_date
        total_days = int(duration.days) + 1
        days = f"{total_days} day" if total_days == 1 else f"{total_days} days"
        event_status = leave_status
        event_text = f"{days} Leave Requested"
        if leave_status in  ["Approved"  , "Rejected"]:
            had_action = True
            event_text = f"{days} Leave {event_status}"
        updates.append(
            {
                "event_type" : "leave request",
                "event_uuid": leave_request_uuid,
                "driver_name": driver_instance.name,
                "driver_profile_image" : driver_instance.profile_image,
                "driver_uuid": driver_uuid , 
                "driver_country_code" : driver_instance.country_code,
                "driver_phone_number": driver_instance.phone_number,
                "vehicle_uuid" : vehicle_instance.vehicle_uuid if vehicle_instance else "",
                "vehicle_number":vehicle_instance.vehicle_number if vehicle_instance else "",
                "start_date": start_date,
                "end_date":end_date,
                "event_status":event_status,
                "event_text" : event_text,
                "had_action":had_action,
                "update_timestamp" : row['requested_at']
            }
        )

    for row in work_requests:
        driver_uuid = str(row['driver_uuid'])
        work_on_off_day_request_uuid = row['work_on_off_day_request_uuid']
        off_date = row['off_date']
        request_status = request_status_dict[row['request_status_uuid']]
        start_date = off_date
        end_date = off_date
        driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : driver_uuid})
        vehicle_instance = await get_tuple_instance(session , VehicleMain , {"mfo_uuid" : mfo_uuid , "driver_uuid" : driver_uuid , "is_enable" : True} , order_by = [desc(VehicleMain.id)] , limit = 1)
        had_action = False
        event_text = f"Extra work Requested"
        event_status = request_status
        if request_status in  ["Approved"  , "Rejected"]:
            had_action = True
            event_text = f"Extra work {event_status}"
        updates.append(
            {
                "event_type" : "work request",
                "event_uuid": work_on_off_day_request_uuid,
                "driver_name": driver_instance.name,
                "driver_profile_image" : driver_instance.profile_image,
                "driver_uuid": driver_uuid , 
                "driver_country_code" : driver_instance.country_code,
                "driver_phone_number": driver_instance.phone_number,
                "vehicle_uuid" : vehicle_instance.vehicle_uuid if vehicle_instance else "",
                "vehicle_number":vehicle_instance.vehicle_number if vehicle_instance else "",
                "start_date": start_date,
                "end_date":end_date,
                "event_status":event_status,
                "event_text" : event_text,
                "had_action":had_action,
                "update_timestamp" : row['requested_at']
            }
        )
        
    updates.sort(key=lambda x: x["update_timestamp"], reverse=True)
    
    dr_updates = []
    
    for up in updates:
        dr_updates.append(
            driver_updates(**up)
        )
   
    
    await session.commit()
    await session.close()
    
    response = get_driver_updates_response(driver_updates = dr_updates)

    return success_response(request, response, message="Fetched all updates requests.")








@mfo_leave_management_router.put("/approveDriverUpdate" , response_model = standard_success_response[approve_driver_update_response] , status_code=200)
async def approveDriverUpdate(req:approve_driver_update_request,
                              background_tasks:BackgroundTasks,
                              request:Request,
                              mfo_uuid = Depends(mfo_role_required()),
                              session:AsyncSession = Depends(get_async_db),
                              session_id: str = Header(..., alias="session-id"),
                              device_id: str = Header(..., alias="device-id")
                              ):
    """
    Approve leave request from the driver.

    Args:
        req (ApproveLeaveRequestRequest): The request body containing leave request uuid.
        request (Request): FastAPI request object.
        mfo_uuid (str): UUID of the authenticated driver (from token).
        session (AsyncSession): Database session.
        session_id (str): Session ID from request headers.
        device_id (str): Device ID from request headers.

    Returns:
        standard_success_response[ApproveLeaveRequestResponse]: API response containing leave details.
    """
    

    if req.event_type == "leave request":
       approved_response =  await approve_leave_request(session , req.event_uuid , mfo_uuid)
    
    elif req.event_type == "work request":
        approved_response = await approve_work_request(session , req.event_uuid , mfo_uuid)
        
    elif req.event_type == "attendance request":
        approved_response = await approve_attendance_request(session , req.event_uuid , mfo_uuid)
    
    
    else:
        raise InvalidRequestError("Invalid Event type")
    
    title = approved_response["title"]
    message = approved_response["message"]
    fcm_token = approved_response["fcm_token"]
    
    background_tasks.add_task(send_fcm_notification, fcm_token ,title , message)
    await session.commit()
    await session.close()

    response = approve_driver_update_response(approve_status = "Request Approved .")
    return success_response(request, response, message="Update approved successfully.")






@mfo_leave_management_router.put("/rejectDriverUpdate" , response_model = standard_success_response[reject_driver_update_response] , status_code=200)
async def rejectDriverUpdate(req:reject_driver_update_request,
                              background_tasks:BackgroundTasks,
                              request:Request,
                              mfo_uuid = Depends(mfo_role_required()),
                              session:AsyncSession = Depends(get_async_db),
                              session_id: str = Header(..., alias="session-id"),
                              device_id: str = Header(..., alias="device-id")
                              ):
    """
    Approve leave request from the driver.

    Args:
        req (ApproveLeaveRequestRequest): The request body containing leave request uuid.
        request (Request): FastAPI request object.
        mfo_uuid (str): UUID of the authenticated driver (from token).
        session (AsyncSession): Database session.
        session_id (str): Session ID from request headers.
        device_id (str): Device ID from request headers.

    Returns:
        standard_success_response[ApproveLeaveRequestResponse]: API response containing leave details.
    """
    

    if req.event_type == "leave request":
       approved_response =  await reject_leave_request(session , req.event_uuid , mfo_uuid)
    
    elif req.event_type == "work request":
        approved_response =await reject_work_request(session , req.event_uuid , mfo_uuid)
        
    elif req.event_type == "attendance request":
        approved_response = await reject_attendance_request(session , req.event_uuid , mfo_uuid)
    
    else:
        raise InvalidRequestError("Invalid Event type")
    
    title = approved_response["title"]
    message = approved_response["message"]
    fcm_token = approved_response["fcm_token"]
    
    background_tasks.add_task(send_fcm_notification, fcm_token ,title , message)
    await session.commit()
    await session.close()

    response = approve_driver_update_response(approve_status = "Request rejected .")
    return success_response(request, response, message="Update rejected successfully.")











@mfo_leave_management_router.get("/getLeaveRequests" , response_model = standard_success_response[GetLeaveRequestsResponse] , status_code=200)
async def getLeaveRequests(request:Request,
                           mfo_uuid = Depends(mfo_role_required()),
                           session:AsyncSession = Depends(get_async_db),
                           session_id: str = Header(..., alias="session-id"),
                           device_id: str = Header(..., alias="device-id")
                           ):
    """
    Retrieve the current month's leave requests details for a mfo.

    Args:
        request (Request): FastAPI request object.
        mfo_uuid (str): UUID of the authenticated driver (from token).
        session (AsyncSession): Database session.
        session_id (str): Session ID from request headers.
        device_id (str): Device ID from request headers.

    Returns:
        standard_success_response[GetLeaveRequestsResponse]: API response containing leave details.
    """
    
    today = get_utc_time()
    leave_requests = await fetch_from_table(
        session,
        DriverLeaveRequest,
        columns=None,
        filters=[
            DriverLeaveRequest.mfo_uuid == mfo_uuid,
            DriverLeaveRequest.start_date >= today,
        ],
        order_by="-id"
    )
    
    leave_types_dict = static_table_settings.static_table_data['LEAVE_TYPES']
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    driver_map = {}
    for row in leave_requests:
        driver_uuid = str(row['driver_uuid'])
        leave = LeaveDetail( 
            leave_request_uuid = row['leave_request_uuid'],
            start_date = row['start_date'],
            end_date = row['end_date'],
            leave_type = leave_types_dict[row['leave_type_uuid']],
            reason = row['reason'],
            leave_status = request_status_dict[row['leave_status_uuid']],
            requested_at = row['requested_at']
        )
        driver_map.setdefault(driver_uuid, []).append(leave)

    drivers_leave_data = [DriverLeave(driver_uuid=uuid, leaves=leaves) for uuid, leaves in driver_map.items()]
    response = GetLeaveRequestsResponse(drivers=drivers_leave_data)
    await session.commit()
    await session.close()

    return success_response(request, response, message="Fetched all drivers' leave requests.")







@mfo_leave_management_router.put("/approveLeaveRequest" , response_model = standard_success_response[ApproveLeaveRequestResponse] , status_code=200)
async def approveLeaveRequest(req:ApproveLeaveRequestRequest,
                              background_tasks:BackgroundTasks,
                              request:Request,
                              mfo_uuid = Depends(mfo_role_required()),
                              session:AsyncSession = Depends(get_async_db),
                              session_id: str = Header(..., alias="session-id"),
                              device_id: str = Header(..., alias="device-id")
                              ):
    """
    Approve leave request from the driver.

    Args:
        req (ApproveLeaveRequestRequest): The request body containing leave request uuid.
        request (Request): FastAPI request object.
        mfo_uuid (str): UUID of the authenticated driver (from token).
        session (AsyncSession): Database session.
        session_id (str): Session ID from request headers.
        device_id (str): Device ID from request headers.

    Returns:
        standard_success_response[ApproveLeaveRequestResponse]: API response containing leave details.
    """
    
    leave_request_instance = await get_tuple_instance(session , DriverLeaveRequest , {"leave_request_uuid" : req.leave_request_uuid})
    
    if not leave_request_instance:
        raise NotFoundError(f"No leave request found with leave_requst_uuid:- {req.leave_request_uuid}")
    
    leave_types_dict = static_table_settings.static_table_data['LEAVE_TYPES']
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    
    approved_status = next((k for k, v in request_status_dict.items() if v == 'Approved'), None)
    leave_request_instance.leave_status_uuid = approved_status
    leave_request_instance.reviewed_by = mfo_uuid
    leave_request_instance.reviewed_at = get_utc_time()
    approved_request_data = { 
        "leave_request_uuid" : leave_request_instance.leave_request_uuid,
        "start_date" : leave_request_instance.start_date,
        "end_date" : leave_request_instance.end_date,
        "leave_type" : leave_types_dict[leave_request_instance.leave_type_uuid],
        "reason" : leave_request_instance.reason,
        "leave_status_uuid" : request_status_dict[leave_request_instance.leave_status_uuid],
        "requested_at" : leave_request_instance.requested_at
    }
    
    
    current_date = leave_request_instance.start_date
    while current_date <= leave_request_instance.end_date:
        leave_data = {
            "leave_request_uuid" : leave_request_instance.leave_request_uuid,
            "driver_uuid" : leave_request_instance.driver_uuid,
            "leave_date" : current_date
        }
        session.add(DriverApprovedLeaves(**leave_data))
        current_date += timedelta(days=1)
        
        
    response = ApproveLeaveRequestResponse(**approved_request_data)
    
    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : leave_request_instance.driver_uuid})
    title = "Leave Request Approved"
    message = f"Your leave from {leave_request_instance.start_date} to {leave_request_instance.end_date} is approved ."
    if leave_request_instance.start_date == leave_request_instance.end_date:
        message = f"Your leave  on {leave_request_instance.end_date} ."
    background_tasks.add_task(send_fcm_notification, driver_instance.fcm_token ,title , message)
    await session.commit()
    await session.close()

    return success_response(request, response, message="Leave request approved successfully.")









@mfo_leave_management_router.put("/rejectLeaveRequest" , response_model = standard_success_response[RejectLeaveRequestResponse] , status_code=200)
async def rejectLeaveRequest(req:RejectLeaveRequestRequest,
                             request:Request,
                             mfo_uuid = Depends(mfo_role_required()),
                             session:AsyncSession = Depends(get_async_db),
                             session_id: str = Header(..., alias="session-id"),
                             device_id: str = Header(..., alias="device-id")
                              ):
    """
    Approve leave request from the driver.

    Args:
        req (RejectLeaveRequestRequest): The request body containing leave request uuid.
        request (Request): FastAPI request object.
        mfo_uuid (str): UUID of the authenticated driver (from token).
        session (AsyncSession): Database session.
        session_id (str): Session ID from request headers.
        device_id (str): Device ID from request headers.

    Returns:
        standard_success_response[RejectLeaveRequestResponse]: API response containing leave details.
    """
    
    leave_request_instance = await get_tuple_instance(session , DriverLeaveRequest , {"leave_request_uuid" : req.leave_request_uuid})
    
    if not leave_request_instance:
        raise NotFoundError(f"No leave request found with leave_requst_uuid:- {req.leave_request_uuid}")
    
    leave_types_dict = static_table_settings.static_table_data['LEAVE_TYPES']
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    
    reject_status = next((k for k, v in request_status_dict.items() if v == 'Rejected'), None)
    leave_request_instance.leave_status_uuid = reject_status
    leave_request_instance.reviewed_by = mfo_uuid
    leave_request_instance.reviewed_at = get_utc_time()
    reject_request_data = { 
        "leave_request_uuid" : leave_request_instance.leave_request_uuid,
        "start_date" : leave_request_instance.start_date,
        "end_date" : leave_request_instance.end_date,
        "leave_type" : leave_types_dict[leave_request_instance.leave_type_uuid],
        "reason" : leave_request_instance.reason,
        "leave_status_uuid" : request_status_dict[leave_request_instance.leave_status_uuid],
        "requested_at" : leave_request_instance.requested_at
    }

    response = RejectLeaveRequestResponse(**reject_request_data)
    await session.commit()
    await session.close()

    return success_response(request, response, message="Leave request rejected successfully")












@mfo_leave_management_router.get("/getWorkOnOffDayRequests" , response_model = standard_success_response[GetWorkOnOffDayRequestsResponse] , status_code=200)
async def getWorkOnOffDayRequests(request:Request,
                                  mfo_uuid = Depends(mfo_role_required()),
                                  session:AsyncSession = Depends(get_async_db),
                                  session_id: str = Header(..., alias="session-id"),
                                  device_id: str = Header(..., alias="device-id")
                                  ):
    
    """
    Retrieve the current month's leave requests details for a mfo.

    Args:
        request (Request): FastAPI request object.
        mfo_uuid (str): UUID of the authenticated driver (from token).
        session (AsyncSession): Database session.
        session_id (str): Session ID from request headers.
        device_id (str): Device ID from request headers.

    Returns:
        standard_success_response[GetWorkOnOffDayRequestsResponse]: API response containing work on off days details.
    """
    
    today = get_utc_time().date()

    work_requests = await fetch_from_table(
        session,
        DriverOffDayWorkRequest,
        columns=None,
        filters=[
            DriverOffDayWorkRequest.mfo_uuid == mfo_uuid,
            DriverOffDayWorkRequest.off_date >= today,
        ],
        order_by="-id"
    )

    
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    
    driver_map = {}
    for row in work_requests:
        driver_uuid = str(row['driver_uuid'])
        work_request = WorkOnOffDaysDetails(
            work_on_off_day_request_uuid = row['work_on_off_day_request_uuid'],
            off_date = row['off_date'],
            reason = row['reason'],
            request_status_uuid = request_status_dict[row['request_status_uuid']],
            requested_at = row['requested_at']
        )
        driver_map.setdefault(driver_uuid, []).append(work_request)

    drivers_work_on_off_day_data = [DriverWorkOnOffDays(driver_uuid=uuid, work_requests=work_request) for uuid, work_request in driver_map.items()]
    response = GetWorkOnOffDayRequestsResponse(drivers=drivers_work_on_off_day_data)
    await session.commit()
    await session.close()

    return success_response(request, response, message="Fetched all drivers' work on off day requests.")







@mfo_leave_management_router.put("/approveWorkOnOffDayRequest" , response_model = standard_success_response[ApproveWorkOnOffDayRequestResponse] , status_code=200)
async def approveWorkOnOffDayRequest(req:ApproveWorkOnOffDayRequestRequest,
                                     background_tasks:BackgroundTasks,
                                     request:Request,
                                     mfo_uuid = Depends(mfo_role_required()),
                                     session:AsyncSession = Depends(get_async_db),
                                     session_id: str = Header(..., alias="session-id"),
                                     device_id: str = Header(..., alias="device-id")
                                     ):
    """
    Approve leave request from the driver.

    Args:
        req (ApproveWorkOnOffDayRequestRequest): The request body containing work on off day request uuid.
        request (Request): FastAPI request object.
        mfo_uuid (str): UUID of the authenticated driver (from token).
        session (AsyncSession): Database session.
        session_id (str): Session ID from request headers.
        device_id (str): Device ID from request headers.

    Returns:
        standard_success_response[ApproveWorkOnOffDayRequestResponse]: API response containing work on off day request details.
    """
    
    work_on_off_day_request_instance = await get_tuple_instance(session , DriverOffDayWorkRequest , {"work_on_off_day_request_uuid" : req.work_on_off_day_request_uuid})
    
    if not work_on_off_day_request_instance:
        raise NotFoundError(f"No work on off day request found with work on off day leave uuid:- {req.work_on_off_day_request_uuid}")
    
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    
    approved_status = next((k for k, v in request_status_dict.items() if v == 'Approved'), None)
    
    work_on_off_day_request_instance.request_status_uuid = approved_status
    work_on_off_day_request_instance.reviewed_by = mfo_uuid
    work_on_off_day_request_instance.reviewed_at = get_utc_time()
    approved_request_data = { 
        "work_on_off_day_request_uuid" : work_on_off_day_request_instance.work_on_off_day_request_uuid,
        "off_date" : work_on_off_day_request_instance.off_date,
        "reason" : work_on_off_day_request_instance.reason,
        "request_status" : request_status_dict[work_on_off_day_request_instance.request_status_uuid],
        "requested_at" : work_on_off_day_request_instance.requested_at
    }
   
    work_req_data = {
        "work_on_off_day_request_uuid" : work_on_off_day_request_instance.work_on_off_day_request_uuid,
        "driver_uuid" : work_on_off_day_request_instance.driver_uuid,
        "work_date":  work_on_off_day_request_instance.off_date
    }
   
    session.add(DriverApprovedOffDayWorks(**work_req_data))

    response = ApproveWorkOnOffDayRequestResponse(**approved_request_data)
    
    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : work_on_off_day_request_instance.driver_uuid})
    title = "Extra Work Request Approved"
    message = f"Your Extra work request on {work_on_off_day_request_instance.off_date} ."
    background_tasks.add_task(send_fcm_notification, driver_instance.fcm_token ,title , message)
    await session.commit()
    await session.close()

    return success_response(request, response, message="Work on off day request approved successfully.")









@mfo_leave_management_router.put("/rejectWorkOnOffDayRequest" , response_model = standard_success_response[RejectWorkOnOffDayRequestResponse] , status_code=200)
async def rejectWorkOnOffDayRequest(req:RejectWorkOnOffDayRequestRequest,
                                    request:Request,
                                    mfo_uuid = Depends(mfo_role_required()),
                                    session:AsyncSession = Depends(get_async_db),
                                    session_id: str = Header(..., alias="session-id"),
                                    device_id: str = Header(..., alias="device-id")
                                    ):
    """
    Approve leave request from the driver.

    Args:
        req (RejectWorkOnOffDayRequestRequest): The request body containing work on off day request uuid.
        request (Request): FastAPI request object.
        mfo_uuid (str): UUID of the authenticated driver (from token).
        session (AsyncSession): Database session.
        session_id (str): Session ID from request headers.
        device_id (str): Device ID from request headers.

    Returns:
        standard_success_response[RejectWorkOnOffDayRequestResponse]: API response containing work on off day request details.
    """
    
    work_on_off_day_request_instance = await get_tuple_instance(session , DriverOffDayWorkRequest , {"work_on_off_day_request_uuid" : req.work_on_off_day_request_uuid})
    
    if not work_on_off_day_request_instance:
        raise NotFoundError(f"No work on off day request found with work on off day leave uuid:- {req.work_on_off_day_request_uuid}")
    
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    reject_status = next((k for k, v in request_status_dict.items() if v == 'Rejected'), None)
        
    work_on_off_day_request_instance.request_status_uuid = reject_status
    work_on_off_day_request_instance.reviewed_by = mfo_uuid
    work_on_off_day_request_instance.reviewed_at = get_utc_time()
    
    reject_request_data = { 
        "work_on_off_day_request_uuid" : work_on_off_day_request_instance.work_on_off_day_request_uuid,
        "off_date" : work_on_off_day_request_instance.off_date,
        "reason" : work_on_off_day_request_instance.reason,
        "request_status" : request_status_dict[work_on_off_day_request_instance.request_status_uuid],
        "requested_at" : work_on_off_day_request_instance.requested_at
    }

    response = RejectWorkOnOffDayRequestResponse(**reject_request_data)
    await session.commit()
    await session.close()

    return success_response(request, response, message="Work on off day request successfully")
