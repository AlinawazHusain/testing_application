from datetime import time, timedelta

from sqlalchemy import desc, func
from config.exceptions import ForbiddenError, NotFoundError
from db.database_operations import get_tuple_instance, insert_into_table
from models.assignment_mapping_models import MfoVehicleMapping
from models.attendace_models import AttendanceRequests, DriverApprovedLeaves, DriverApprovedOffDayWorks, DriverAttendance, DriverLeaveRequest, DriverOffDayWorkRequest
from models.driver_models import DriverMain
from settings.static_data_settings import static_table_settings
from utils.attendance_utils import driver_on_extra_day_work
from utils.time_utils import convert_utc_to_ist, get_utc_time


async def approve_leave_request(session , leave_request_uuid , mfo_uuid):
    leave_request_instance = await get_tuple_instance(session , DriverLeaveRequest , {"leave_request_uuid" : leave_request_uuid})
    
    if not leave_request_instance:
        raise NotFoundError(f"No leave request found with leave_requst_uuid:- {leave_request_uuid}")
    
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    
    approved_status = next((k for k, v in request_status_dict.items() if v == 'Approved'), None)
    leave_request_instance.leave_status_uuid = approved_status
    leave_request_instance.reviewed_by = mfo_uuid
    leave_request_instance.reviewed_at = get_utc_time()
    
    
    current_date = leave_request_instance.start_date
    while current_date <= leave_request_instance.end_date:
        leave_data = {
            "leave_request_uuid" : leave_request_instance.leave_request_uuid,
            "driver_uuid" : leave_request_instance.driver_uuid,
            "leave_date" : current_date
        }
        session.add(DriverApprovedLeaves(**leave_data))
        current_date += timedelta(days=1)
    
    title = "Leave Request Approved"
    message = f"Your leave from {leave_request_instance.start_date} to {leave_request_instance.end_date} is approved ."
    if leave_request_instance.start_date == leave_request_instance.end_date:
        message = f"Your leave  on {leave_request_instance.end_date}  is approved."
    
    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : leave_request_instance.driver_uuid})
    
    return {
        "title" : title,
        "message" : message,
        "fcm_token" : driver_instance.fcm_token
    }
    
    
    
    


async def approve_work_request(session , work_on_off_day_request_uuid , mfo_uuid):
    work_on_off_day_request_instance = await get_tuple_instance(session , DriverOffDayWorkRequest , {"work_on_off_day_request_uuid" : work_on_off_day_request_uuid})
    
    if not work_on_off_day_request_instance:
        raise NotFoundError(f"No work on off day request found with work on off day leave uuid:- {work_on_off_day_request_uuid}")
    
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    
    approved_status = next((k for k, v in request_status_dict.items() if v == 'Approved'), None)
    
    work_on_off_day_request_instance.request_status_uuid = approved_status
    work_on_off_day_request_instance.reviewed_by = mfo_uuid
    work_on_off_day_request_instance.reviewed_at = get_utc_time()
   
    work_req_data = {
        "work_on_off_day_request_uuid" : work_on_off_day_request_instance.work_on_off_day_request_uuid,
        "driver_uuid" : work_on_off_day_request_instance.driver_uuid,
        "work_date":  work_on_off_day_request_instance.off_date
    }
   
    session.add(DriverApprovedOffDayWorks(**work_req_data))

    
    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : work_on_off_day_request_instance.driver_uuid})
    title = "Extra Work Request Approved"
    message = f"Your Extra work request on {work_on_off_day_request_instance.off_date} is approved."
    
    return {
        "title" : title,
        "message" : message,
        "fcm_token" : driver_instance.fcm_token
    }
    
    
    
    
    

async def approve_attendance_request(session , attendance_request_uuid , mfo_uuid):
    attendance_request_instance = await get_tuple_instance(session , AttendanceRequests , {"attendance_request_uuid" : attendance_request_uuid})
    
    if not attendance_request_instance:
        raise NotFoundError(f"No attendance request found with attendance requesst uuid:- {attendance_request_uuid}")
    
    attendance_request_instance.attendance_request_status = "Approved"
   
    
    attendance = await get_tuple_instance(
                    session,
                    DriverAttendance,
                    {'driver_uuid': attendance_request_instance.driver_uuid},
                    extra_conditions=[
                        func.DATE(convert_utc_to_ist(DriverAttendance.attendance_trigger_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
                    ],
                    order_by=[desc(DriverAttendance.id)],
                    limit=1  
                )
    if attendance:
        mapping_exist = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : attendance_request_instance.driver_uuid , "is_enable" : True})
        if mapping_exist:
            attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
            no_action_attendance_state_uuid = next((k for k, v in attendance_states_dict.items() if v == 'No action'), None)
            drive_vehicle_connected_time_states_dict = static_table_settings.static_table_data['DRIVER_VEHICLE_CONNECTED_TIME_STATES']
            no_action_time_state_uuid = next((k for k, v in drive_vehicle_connected_time_states_dict.items() if v == 'No action'), None)
            on_extra_day = await driver_on_extra_day_work(session , attendance_request_instance.driver_uuid)
            attendance_data = {
                "driver_uuid" : attendance_request_instance.driver_uuid,
                "again_requested" : True,
                "vehicle_uuid" : mapping_exist.vehicle_uuid,
                'mfo_uuid' : attendance.mfo_uuid,
                "attendance_state_uuid" : no_action_attendance_state_uuid,
                "attendance_trigger_time" : get_utc_time(),
                "expected_time_stamp" : time(0, 30, 0),
                "driver_attendance_vehicle_connected_time_state_uuid" : no_action_time_state_uuid,
                "extra_day_work" : on_extra_day
            }
            await insert_into_table(session , DriverAttendance , attendance_data)


    else:
        raise ForbiddenError("Driver is not eligilble to do work Today")
    
    
    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : attendance_request_instance.driver_uuid})
    title = "Attendance Request Approved"
    message = f"Your Attendance request on for today is approved , Mark your attendance now."
    
    return {
        "title" : title,
        "message" : message,
        "fcm_token" : driver_instance.fcm_token
    }
    
    
    
    
    



async def reject_leave_request(session , leave_request_uuid , mfo_uuid):
    leave_request_instance = await get_tuple_instance(session , DriverLeaveRequest , {"leave_request_uuid" : leave_request_uuid})
    
    if not leave_request_instance:
        raise NotFoundError(f"No leave request found with leave_requst_uuid:- {leave_request_uuid}")
    
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    
    reject_status = next((k for k, v in request_status_dict.items() if v == 'Rejected'), None)
    leave_request_instance.leave_status_uuid = reject_status
    leave_request_instance.reviewed_by = mfo_uuid
    leave_request_instance.reviewed_at = get_utc_time()
    
    
    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : leave_request_instance.driver_uuid})
    title = "Leave Request Rejected"
    message = f"Your leave from {leave_request_instance.start_date} to {leave_request_instance.end_date} is rejected ."
    if leave_request_instance.start_date == leave_request_instance.end_date:
        message = f"Your leave  on {leave_request_instance.end_date}  is rejected."
    
    return {
        "title" : title,
        "message" : message,
        "fcm_token" : driver_instance.fcm_token
    }
    
    

async def reject_work_request(session ,work_on_off_day_request_uuid ,  mfo_uuid):
    work_on_off_day_request_instance = await get_tuple_instance(session , DriverOffDayWorkRequest , {"work_on_off_day_request_uuid" : work_on_off_day_request_uuid})
    
    if not work_on_off_day_request_instance:
        raise NotFoundError(f"No work on off day request found with work on off day leave uuid:- {work_on_off_day_request_uuid}")
    
    request_status_dict = static_table_settings.static_table_data['REQUEST_STATUSES']
    reject_status = next((k for k, v in request_status_dict.items() if v == 'Rejected'), None)
        
    work_on_off_day_request_instance.request_status_uuid = reject_status
    work_on_off_day_request_instance.reviewed_by = mfo_uuid
    work_on_off_day_request_instance.reviewed_at = get_utc_time()
    
    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : work_on_off_day_request_instance.driver_uuid})
    title = "Extra Work Request Rejected"
    message = f"Your Extra work request on {work_on_off_day_request_instance.off_date} is rejected."
    
    return {
        "title" : title,
        "message" : message,
        "fcm_token" : driver_instance.fcm_token
    }
    
    
    
    

async def reject_attendance_request(session , attendance_request_uuid , mfo_uuid):
    attendance_request_instance = await get_tuple_instance(session , AttendanceRequests , {"attendance_request_uuid" : attendance_request_uuid})
    
    if not attendance_request_instance:
        raise NotFoundError(f"No attendance request found with attendance requesst uuid:- {attendance_request_uuid}")
    
    attendance_request_instance.attendance_request_status = "Rejected"

    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : attendance_request_instance.driver_uuid})
    title = "Attendance Request Approved"
    message = f"Your Attendance request on for today is rejected by MFO"
    
    return {
        "title" : title,
        "message" : message,
        "fcm_token" : driver_instance.fcm_token
    }
    