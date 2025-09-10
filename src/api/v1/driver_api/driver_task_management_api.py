from fastapi import APIRouter , Depends, Header, Request 
from sqlalchemy import asc, desc, func, select
from auth.dependencies import driver_role_required
from config.exceptions import NotFoundError
from db.database_operations import fetch_from_table, get_tuple_instance
from models.assignment_mapping_models import MfoVehicleMapping
from models.attendace_models import AttendanceRequests, DriverAttendance
from models.incentive_models import DailyDriverIncentive, DriverDailyTasks
from models.porter_models import AvaronnPorterTrip
from models.task_management_models import Tasks
from schemas.v1.standard_schema import standard_success_response
from schemas.v1.driver_schemas.driver_task_management_schema import (
    Task, currentPorterTrip , get_tasks_response
    )
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from settings.static_data_settings import static_table_settings
from utils.driver_incentive_utils import get_points_to_earn_on_task
from utils.response import success_response
from utils.time_utils import convert_utc_to_ist, get_utc_time



driver_task_management_router = APIRouter()






@driver_task_management_router.get("/getTasks" , response_model= standard_success_response[get_tasks_response] , status_code = 200)
async def getTasks(request:Request,
                   driver_uuid = Depends(driver_role_required()),
                    session:AsyncSession = Depends(get_async_db),
                    session_id: str = Header(..., alias="session-id"),
                    device_id: str = Header(..., alias="device-id")
                    ):
    vehicle_instance = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : driver_uuid , "is_enable" : True})
    attendance_trigger_time = None
    incentive_earned_today = 0
    if vehicle_instance:
        tasks  = await fetch_from_table(session , Tasks , None , {"vehicle_uuid" : vehicle_instance.vehicle_uuid})
        present_status = False
        have_attendance = False
        have_pending_request = False
        attendance = None
        vehicle_connected_status = False
        task_list = []
        if tasks:
            for task in tasks:
                model_types_dict = static_table_settings.static_table_data['MODEL_TYPES']
                sub_model_types_dict = static_table_settings.static_table_data['SUB_MODEL_TYPES']
                curr_task = Task(
                    model_type = model_types_dict[task['model_type']],
                    sub_model_type= sub_model_types_dict[task['sub_model_type']],
                    task_start_time = convert_utc_to_ist(task['task_start_time']),
                    task_end_time= convert_utc_to_ist(task['task_end_time'])
                )
                task_list.append(curr_task)
                
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
            attendance_status_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
            present_marked_uuid = next((k for k, v in attendance_status_dict.items() if v == 'Present'), None)
            expired_uuid = next((k for k, v in attendance_status_dict.items() if v == 'Expired'), None)
            absent_uuid = next((k for k, v in attendance_status_dict.items() if v == 'Absent'), None)
        if attendance:
            have_attendance = True
            if attendance.attendance_state_uuid == expired_uuid or attendance.attendance_state_uuid == absent_uuid:
                have_attendance = False
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
                    have_pending_request = True
                    
            attendance_trigger_time = convert_utc_to_ist(attendance.attendance_trigger_time)
            vehicle_connected_status = True if attendance.bluetooth_connection_time else False
            if attendance.attendance_state_uuid == present_marked_uuid:
                have_attendance = True
                present_status  = True
                
        
        daily_incentive_instance = await get_tuple_instance(
                                session,
                                DailyDriverIncentive,
                                {'driver_uuid': driver_uuid},
                                extra_conditions=[
                                    func.DATE(DailyDriverIncentive.trip_date) == func.DATE(get_utc_time())
                                ],
                                order_by=[desc(DailyDriverIncentive.id)],
                                limit=1  
                            )
        
        if daily_incentive_instance:
            incentive_earned_today = daily_incentive_instance.final_incentive
        
        
        query = select(AvaronnPorterTrip).where(
            AvaronnPorterTrip.driver_uuid == driver_uuid,
            func.DATE(AvaronnPorterTrip.trip_on_time) == func.DATE(get_utc_time())
        ).order_by(
            asc(AvaronnPorterTrip.id)
        )
        result = await session.execute(query)
        trips = result.scalars().all()
        current_trip = {}
        for trip in trips:
            if trip.trip_off_time is None:
                trip_data = {
                    "porter_trip_uuid" : trip.avaronn_porter_trip_uuid,
                    "porter_trip_on_time": convert_utc_to_ist(trip.trip_on_time) if trip.trip_on_time else None,
                }
                current_time = get_utc_time()
                interval = current_time - trip.trip_on_time
                total_seconds = int(interval.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                trip_data['current_porter_trip_running_time'] = f"{hours:02}:{minutes:02}:{seconds:02}"
                
                current_trip = trip_data
                
        query3 = select(
            func.COALESCE(func.SUM(DriverDailyTasks.points_earned), 0).label("points_earned"),
        ).where(
            DriverDailyTasks.driver_uuid == driver_uuid,
            func.DATE(DriverDailyTasks.completed_at) == func.DATE(get_utc_time())
        )

        result3 = await session.execute(query3)
        points_data = result3.fetchone()
        points_earned_today = points_data.points_earned
        
        task_event = "Reach Hotspot"
        
        if not vehicle_connected_status:
            task_event = "Vehicle Reaching On_time"  
            
        if not present_status :
            task_event = "Attendance" 
            
         
        points_to_earn_on_task = await get_points_to_earn_on_task(task_event)
        
        trip_event = "Trip start" if not current_trip else "Trip off"
        points_to_earn_on_trip = await get_points_to_earn_on_task(trip_event)
        await session.commit()
        await session.close()
        data_res = get_tasks_response(
            points_earned_today=points_earned_today,
            incentive_earned_today = incentive_earned_today,
            have_attendance = have_attendance,
            have_pending_request = have_pending_request,
            present_status = present_status,
            attendance_trigger_time = attendance_trigger_time,
            vehicle_connected_status= vehicle_connected_status,
            vehicle_uuid = attendance.vehicle_uuid if attendance else None,
            points_to_earn_on_task = points_to_earn_on_task,
            tasks = task_list,
            current_trip = currentPorterTrip(**current_trip),
            points_to_earn_on_trip = points_to_earn_on_trip
        )
        
        return success_response(request , data_res , message = "Tasks get successfully")
    
    else:
        raise NotFoundError("No Vehicle Assigned")
    
