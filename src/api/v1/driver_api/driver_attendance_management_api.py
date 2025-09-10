from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request 
from datetime import datetime, time, timedelta
from sqlalchemy import desc, func, select
from auth.dependencies import driver_role_required
from config.exceptions import ForbiddenError, NotFoundError
from config.firebase_config import send_fcm_notification
from db.database_operations import get_tuple_instance, insert_into_table
from models.assignment_mapping_models import MfoVehicleMapping
from models.attendace_models import AttendanceRequests, DriverAttendance, DriverAttendanceSummary
from models.driver_models import DriverMain
from models.mfo_models import MfoMain
from models.vehicle_hub_models import HubAddressBook, VehicleHubMapping
from models.vehicle_models import VehicleLocation, VehicleMain
from schemas.v1.standard_schema import standard_success_response
from schemas.v1.driver_schemas.driver_attendance_schema import (
    bluetooth_connected_request, bluetooth_connected_response,
    get_attendance_status_response, have_attendance_response,
    mark_absent_request, mark_absent_response, mark_present_request,
    mark_present_response, request_new_attendance_response
)
from settings.static_data_settings import static_table_settings
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from utils.attendance_utils import driver_on_extra_day_work
from utils.driver_activity_rule_engine import haversine
from utils.driver_incentive_utils import get_incentive_points
from utils.leave_management_utils import get_monthly_required_working_days
from utils.response import success_response
from utils.time_utils import convert_utc_to_ist, get_utc_time



driver_attendance_management_router = APIRouter()





@driver_attendance_management_router.put("/markPresent" , response_model= standard_success_response[mark_present_response])
async def mark_present(request:Request,
                       req: mark_present_request,
                        driver_uuid = Depends(driver_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    
    mark_attendance_time = get_utc_time().time()
    attendance = await get_tuple_instance(
            session,
            DriverAttendance,
            {'driver_uuid': driver_uuid},
            extra_conditions=[
                func.DATE(DriverAttendance.attendance_trigger_time) == func.DATE(get_utc_time())
            ],
            order_by=[desc(DriverAttendance.id)],
            limit=1  
        )
    
    if not attendance:
        raise NotFoundError("No Attendance Found")
    
    attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
    present_state_uuid = next((k for k, v in attendance_states_dict.items() if v == 'Present'), None)
    vehicle_status_dict = static_table_settings.static_table_data["VEHICLE_STATUS"]
    idle_status = next((k for k, v in vehicle_status_dict.items() if v == 'Idle'), None)
    
    if attendance.attendance_state_uuid == present_state_uuid:
        await session.commit()
        await session.close()
        data_res = mark_present_response(
            marked = True,
            points_earned = 0
        )
        return success_response(request , data_res , message = "Present marked successfully")

    
    
    attendance.driver_attandence_location_lat = req.driver_lat
    attendance.driver_attandence_location_lng = req.driver_lng
    attendance.attendance_time = mark_attendance_time
    attendance.attendance_state_uuid = present_state_uuid
    
    today = get_utc_time()
    month = today.month
    year = today.year
    driver_attendance_summary_instance = await get_tuple_instance(session ,
                                                                 DriverAttendanceSummary ,
                                                                 {"driver_uuid" : driver_uuid,
                                                                  "month" : month,
                                                                  "year" : year 
                                                                  })
    if driver_attendance_summary_instance:
        if attendance.extra_day_work:
            driver_attendance_summary_instance.total_worked_on_leave_days +=1
            driver_attendance_summary_instance.final_achieved_days +=1
        else:
            driver_attendance_summary_instance.total_present_days += 1
            driver_attendance_summary_instance.final_achieved_days +=1
    
    else:
        required_working_days = await get_monthly_required_working_days(session , driver_uuid , year , month)
        next_month_data = {
                "driver_uuid": driver_uuid, 
                "year" : year ,
                "month" : month,
                "final_achieved_days" : 1,
                "required_working_days" : required_working_days
            }
        if attendance.extra_day_work:
            next_month_data["total_worked_on_leave_days"] = 1
        else:
            next_month_data["total_present_days"] = 1
        
        await insert_into_table(session , DriverAttendanceSummary ,next_month_data)
    
    vehicle_main_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : attendance.vehicle_uuid , "is_enable" : True})
    vehicle_main_instance.vehicle_status = idle_status
    points_earned  = await get_incentive_points(session ,driver_uuid  , vehicle_main_instance.vehicle_uuid , vehicle_main_instance.mfo_uuid , "Attendance")
    await session.commit()
    await session.close()
    
    data_res = mark_present_response(
        marked = True,
        points_earned = points_earned
    )
    return success_response(request , data_res , message = "Present marked successfully")
        

        
        
        

@driver_attendance_management_router.put("/markAbsent" , response_model= standard_success_response[mark_absent_response])
async def mark_absent(request:Request,
                      background_tasks:BackgroundTasks,
                      req: mark_absent_request,
                      driver_uuid = Depends(driver_role_required()),
                      session:AsyncSession = Depends(get_async_db),
                      session_id: str = Header(..., alias="session-id"),
                      device_id: str = Header(..., alias="device-id")
                      ):
    
    mark_attendance_time = get_utc_time().time()
    
    attendance = await get_tuple_instance(
            session,
            DriverAttendance,
            {'driver_uuid': driver_uuid},
            extra_conditions=[
                func.DATE(convert_utc_to_ist(DriverAttendance.attendance_trigger_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
            ],
            order_by=[desc(DriverAttendance.id)],
            limit=1  
        )
    
    if not attendance:
        raise NotFoundError("No Attendance Found")

    attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
    absent_state_uuid = next((k for k, v in attendance_states_dict.items() if v == 'Absent'), None)
    
    
    attendance.driver_attandence_location_lat = req.driver_lat
    attendance.driver_attandence_location_lng = req.driver_lng
    attendance.attendance_time = mark_attendance_time
    attendance.attendance_state_uuid = absent_state_uuid
    session.add(attendance)
    
    vehicle_status_dict = static_table_settings.static_table_data["VEHICLE_STATUS"]
    idle_status = next((k for k, v in vehicle_status_dict.items() if v == 'Idle'), None)
    vehicle_main_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : attendance.vehicle_uuid , "is_enable" : True})
    vehicle_main_instance.vehicle_status = idle_status
    
    mfo_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : attendance.mfo_uuid , "is_enable" : True})
    title = "Review Required: Driver Not Comming Today"
    message = f"A Driver has marked absent . Please review and take action."
    background_tasks.add_task(send_fcm_notification, mfo_instance.fcm_token ,title , message)
    
    await session.commit()
    await session.close()
    data_res =  mark_absent_response(
        marked = True
    )
    return success_response(request , data_res , message = "Absent marked successfully")




@driver_attendance_management_router.get("/haveAttendance" , response_model= standard_success_response[have_attendance_response])
async def have_attendance(request:Request,
                          driver_uuid = Depends(driver_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                      ):
    
    query = select(DriverAttendance).where(
    DriverAttendance.driver_uuid == driver_uuid,
    func.DATE(convert_utc_to_ist(DriverAttendance.attendance_trigger_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
    ).order_by(
    desc(DriverAttendance.id) 
    ).limit(1)
    result = await session.execute(query)
    attendance = result.scalars().first()
    attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
    no_action_state_uuid = next((k for k, v in attendance_states_dict.items() if v == 'No action'), None)
    have_attendance = False
    if attendance and attendance.attendance_state_uuid == no_action_state_uuid:
        have_attendance = True
            
        
    await session.close()
    data_res = have_attendance_response(
        have_attendance=have_attendance
    )
    return success_response(request , data_res , message = "Attendance Fetched successfully")
        
    




@driver_attendance_management_router.get("/attendanceStatus" , response_model= standard_success_response[get_attendance_status_response])
async def attendance_status(request:Request,
                            driver_uuid = Depends(driver_role_required()),
                            session:AsyncSession = Depends(get_async_db),
                            session_id: str = Header(..., alias="session-id"),
                            device_id: str = Header(..., alias="device-id")
                            ):
    
    query = select(DriverAttendance).where(
    DriverAttendance.driver_uuid == driver_uuid,
    func.DATE(convert_utc_to_ist(DriverAttendance.attendance_trigger_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
    ).order_by(
    desc(DriverAttendance.id) 
    ).limit(1)

    result = await session.execute(query)
    attendance = result.scalars().first()
    
    data = (
    {key: value  
    for key, value in vars(attendance).items() if not key.startswith("_")}
    if attendance else None
    )
    have_attendance_status = False
    if data:
        have_attendance_status = True
        attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
        data['attendance_status'] = attendance_states_dict[data['attendance_state_uuid']]
        await session.commit()
        await session.close()
        data['attendance_trigger_time'] = convert_utc_to_ist(data['attendance_trigger_time']).isoformat()
        if data['attendance_time']:
            data['attendance_time'] = (datetime.combine(datetime.today(), data['attendance_time']) + timedelta(hours=5 , minutes = 30)).time()
    else:
        data = {
            "attendance_status" : "No attendence found"
        }
    data_res =  get_attendance_status_response(
        have_attendance_status = have_attendance_status,
        attendance_mark_time = data.get('attendance_time' , None),
        attendance_status = data['attendance_status']
    )
    return success_response(request , data_res , message = "Attendance status fetched successfully")
        
    





@driver_attendance_management_router.put("/bluetoothConnected" , response_model=standard_success_response[bluetooth_connected_response])
async def bluetoothConnected(request:Request,
                             background_tasks:BackgroundTasks,
                             req: bluetooth_connected_request,
                             driver_uuid = Depends(driver_role_required()),
                             session:AsyncSession = Depends(get_async_db),
                             session_id: str = Header(..., alias="session-id"),
                             device_id: str = Header(..., alias="device-id")
                             ):
    
    current_time = get_utc_time()
    time_5_mins_before = current_time - timedelta(minutes=5)
    bluetooth_connection_time = get_utc_time().time()
    attendance_trigger_time = None
    attendance = await get_tuple_instance(
            session,
            DriverAttendance,
            {'driver_uuid': driver_uuid},
            extra_conditions=[
                func.DATE(convert_utc_to_ist(DriverAttendance.attendance_trigger_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
            ],
            order_by=[desc(DriverAttendance.id)],
            limit=1  
        )
    
    if not attendance:
        raise NotFoundError("No Attendance Found")
    driver_attendance_vehicle_connected_time_states_dict = static_table_settings.static_table_data["DRIVER_VEHICLE_CONNECTED_TIME_STATES"]
    connect_time_state_uuid = None
    
    points_earned  = 0
    
    vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" :attendance.vehicle_uuid })
    # vehicle_location = await get_tuple_instance(session ,
    #                                             VehicleLocation ,
    #                                             {"vehicle_number" : vehicle_instance.vehicle_number},
    #                                             order_by=[desc(VehicleLocation.id)],
    #                                             limit = 1
    #                                             )
    
    # if vehicle_location and vehicle_location.created_at >= time_5_mins_before:
    #     vehicle_to_driver_distance = await haversine(vehicle_location.lat , vehicle_location.lng , req.driver_lat , req.driver_lng)
    #     if vehicle_to_driver_distance >100:
    #         raise ForbiddenError("Go near vehicle to connect")
        
    # else:
    #     vehicle_hub_mapping = await get_tuple_instance(session , 
    #                                                    VehicleHubMapping ,
    #                                                    {"vehicle_uuid" : attendance.vehicle_uuid , "is_enable" : True},
    #                                                    order_by=[desc(VehicleHubMapping.id)],
    #                                                    limit = 1 
    #                                                    )
    #     if vehicle_hub_mapping:
    #         hub_instance = await get_tuple_instance(session , HubAddressBook ,{"hub_address_book_uuid" : vehicle_hub_mapping.hub_address_book_uuid} )
    #         if hub_instance:
    #             hub_to_driver_distance = await haversine(hub_instance.hub_lat , hub_instance.hub_lat , req.driver_lat , req.driver_lng)
    #             if hub_to_driver_distance >100:
    #                 raise ForbiddenError("Go Near Hub to connect vehicle")
                
    attendance_trigger_time = attendance.attendance_trigger_time
    if attendance and bluetooth_connection_time <= attendance_trigger_time.time():
        connect_time_state_uuid = next((k for k, v in driver_attendance_vehicle_connected_time_states_dict.items() if v == 'On time'), None)
        points_earned  = await get_incentive_points(session ,driver_uuid  , attendance.vehicle_uuid ,attendance.mfo_uuid, "Vehicle Reaching On_time")
        
    else:
        connect_time_state_uuid = next((k for k, v in driver_attendance_vehicle_connected_time_states_dict.items() if v == 'Late'), None)
    
    attendance.driver_attendance_vehicle_location_lat = req.driver_lat
    attendance.driver_attendance_vehicle_location_lng = req.driver_lng
    attendance.bluetooth_connection_time = bluetooth_connection_time
    attendance.driver_attendance_vehicle_connected_time_state_uuid = connect_time_state_uuid
    
    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : driver_uuid})
    vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid":attendance.vehicle_uuid })
    mfo_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : attendance.mfo_uuid , "is_enable" : True})
    title = "Driver Arrival Confirmed"
    message = f"Driver {driver_instance.name} successfully connected the vehicle {vehicle_instance.vehicle_number}."
    background_tasks.add_task(send_fcm_notification, mfo_instance.fcm_token ,title , message)
    
    await session.commit()
    await session.close()
    data_res =  bluetooth_connected_response(
        connected = True,
        points_earned = points_earned
    )
    return success_response(request , data_res , message = "Bluetooth connected successfully")
    
    
    


@driver_attendance_management_router.get("/requestNewAttendance" , response_model= standard_success_response[request_new_attendance_response])
async def request_new_attendance(request:Request,
                                 background_tasks:BackgroundTasks,
                                 driver_uuid = Depends(driver_role_required()),
                                 session:AsyncSession = Depends(get_async_db),
                                 session_id: str = Header(..., alias="session-id"),
                                 device_id: str = Header(..., alias="device-id")
                                 ):
    attendance = await get_tuple_instance(
                    session,
                    DriverAttendance,
                    {'driver_uuid': driver_uuid},
                    extra_conditions=[
                        func.DATE(convert_utc_to_ist(DriverAttendance.attendance_trigger_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
                    ],
                    order_by=[desc(DriverAttendance.id)],
                    limit=1  
                )
    if attendance:
        mapping_exist = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : driver_uuid , "is_enable" : True})
        requested = False
        if mapping_exist:
            att_req_data = {
                "driver_uuid" : driver_uuid,
                "vehicle_uuid" : attendance.vehicle_uuid,
                "mfo_uuid" : attendance.mfo_uuid
            }
            request_pending = await get_tuple_instance(
                    session,
                    AttendanceRequests,
                    {'driver_uuid': driver_uuid},
                    extra_conditions=[
                        func.DATE(convert_utc_to_ist(AttendanceRequests.created_at)) == func.DATE(convert_utc_to_ist(get_utc_time()))
                    ],
                    order_by=[desc(AttendanceRequests.id)],
                    limit=1  )
            
            if request_pending and request_pending.attendance_request_status == "Pending":
                    raise ForbiddenError("Already a Attendance request in Pending , wait for MFO to accept or reject")
            await insert_into_table(session , AttendanceRequests, att_req_data)
            requested = True
            mfo_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : attendance.mfo_uuid})
            driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : driver_uuid})
            fcm_token = mfo_instance.fcm_token
            title = "Attendance Request"
            message = f"Driver {driver_instance.name} requested for attendance , take action on request"
            background_tasks.add_task(send_fcm_notification, fcm_token ,title , message)
        await session.commit()
        await session.close()
    
    else:
        await session.close()
        raise NotFoundError("No Today's Attendance Found")
    
    data_res =  request_new_attendance_response(
        requested = requested,
        reason= "Vehicle Assigned to another driver" if not requested else ""
    )
    return success_response(request , data_res , message = "New Attendance requested successfully")