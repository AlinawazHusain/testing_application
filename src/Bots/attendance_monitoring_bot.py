import asyncio
from config.firebase_config import send_fcm_notification
from sqlalchemy import select, func
from db.database_operations import get_tuple_instance
from db.db import get_async_db
from models.attendace_models import DriverAttendance
from models.driver_models import DriverMain
from models.mfo_models import MfoMain
from models.vehicle_models import VehicleMain
from settings.static_data_settings import static_table_settings
from utils.time_utils import convert_utc_to_ist, get_utc_time
from datetime import datetime, time

async def monitor_attendances():
    attendance_status_dict = static_table_settings.static_table_data["ATTENDANCE_STATES"]

    no_action_uuid = next((k for k, v in attendance_status_dict.items() if v == 'No action'), None)
    expired_uuid = next((k for k, v in attendance_status_dict.items() if v == 'Expired'), None)
    absent_uuid = next((k for k, v in attendance_status_dict.items() if v == 'Absent'), None)
    while True:
        try:
            async for session in get_async_db():
                now = convert_utc_to_ist(get_utc_time())
                today = now.date()
                
                today_730 = datetime.combine(today, time(7, 30))
                query = select(DriverAttendance).where(
                    func.date(DriverAttendance.attendance_trigger_time) == today,
                    DriverAttendance.attendance_state_uuid == no_action_uuid
                )

                result = await session.execute(query)
                attendances = result.scalars().all()
                for attendance in attendances:
                    if attendance.attendance_trigger_time < now:
                        if attendance.attendance_state_uuid == expired_uuid:
                            attendance.attendance_state_uuid = absent_uuid
                            driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : attendance.driver_uuid})
                            vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : attendance.vehicle_uuid})
                            mfo_main = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : vehicle_instance.mfo_uuid})
                            title = "Attendance update"
                            body = f"Driver - {driver_instance.name} assigned with vehicle - {vehicle_instance.vehicle_number} is Absent Today."
                            body_driver = f"Yout today's attendance for vehicle {vehicle_instance.vehicle_number} is marked Absent no action on attendance."
                            send_fcm_notification(mfo_main.fcm_token , title , body)
                            send_fcm_notification(driver_instance.fcm_token , title , body_driver)
                        else:
                            attendance.attendance_state_uuid = expired_uuid
                            driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : attendance.driver_uuid})
                            vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : attendance.vehicle_uuid})
                            mfo_main = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : vehicle_instance.mfo_uuid})
                            title = "Attendance Expiration"
                            body = f"Attendance of Driver - {driver_instance.name} assigned with vehicle - {vehicle_instance.vehicle_number} is expired due to no action before trigger time"
                            body_driver = f"Your today's attendance for vehicle {vehicle_instance.vehicle_number} is expired due to no action before trigger time"
                            send_fcm_notification(mfo_main.fcm_token , title , body)
                            send_fcm_notification(driver_instance.fcm_token , title , body_driver)
                    
                    elif today_730 <= now and attendance.attendance_state_uuid == no_action_uuid:
                        driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : attendance.driver_uuid})
                        vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : attendance.vehicle_uuid})
                        title = "Today's Attendance"
                        body = f"Your today's attendance on vehicle - {vehicle_instance.vehicle_number} is awaiting for your action. Mark it now"
                        send_fcm_notification(driver_instance.fcm_token , title , body)

                await session.commit()
                await session.close()

        except Exception as e:
            print(f"Error occurred in attendance monitoring bot: {e}")

        await asyncio.sleep(15 * 60)
