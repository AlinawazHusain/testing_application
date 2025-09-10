from datetime import datetime, time

from sqlalchemy import desc, func, text
from db.database_operations import get_tuple_instance, insert_into_table
from models.hotspot_routes_models import HotspotRoutes
from models.porter_models import AvaronnPorterTrip
from models.vehicle_models import VehicleMain
from settings.static_data_settings import static_table_settings

from models.attendace_models import DriverWorkingPolicy, DriverAttendance, DriverPolicy
from utils.time_utils import convert_utc_to_ist, get_utc_time


async def create_attendance(session , driver_uuid , vehicle_uuid, mfo_uuid , attendance_trigger_time = None):
    if not attendance_trigger_time:
       attendance_trigger_time = datetime.combine(datetime.today(), time(9, 30, 0))
    
    attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
    driver_vehicle_connected_time_state_dict = static_table_settings.static_table_data['DRIVER_VEHICLE_CONNECTED_TIME_STATES']
    no_action_attendance_status_uuid = next((k for k,v in attendance_states_dict.items() if v == "No action") , None)
    no_action_driver_attendance_vehicle_connected_time_state_uuid = next((k for k , v in driver_vehicle_connected_time_state_dict.items() if v == "No action") , None)

    new_attendence = DriverAttendance(
        mfo_uuid = mfo_uuid,
        vehicle_uuid = vehicle_uuid,
        driver_uuid = driver_uuid,
        attendance_trigger_time = attendance_trigger_time,
        attendance_state_uuid = no_action_attendance_status_uuid,
        expected_time_stamp = time(0, 30, 0),
        driver_attendance_vehicle_connected_time_state_uuid = no_action_driver_attendance_vehicle_connected_time_state_uuid
        )
    session.add(new_attendence)
    return


async def create_driver_policy(session , driver_uuid , mfo_uuid):
    
    policy_instance = await insert_into_table(session , DriverPolicy , {"sunday_working" : False})
    driver_working_policy = DriverWorkingPolicy(
        driver_uuid = driver_uuid,
        mfo_uuid = mfo_uuid,
        driver_policy_uuid  = policy_instance.driver_policy_uuid,
        valid_from = get_utc_time()
    )
        
    session.add(driver_working_policy)
     
    
    
    
    

async def get_driver_status_and_current_activity(session , driver_uuid):
    attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
    driver_status = "On Leave"
    driver_current_activity = "No status found"
    
    vehicle_instance = await get_tuple_instance(session , VehicleMain , {"driver_uuid" : driver_uuid , "is_enable" : True})
    
    if not vehicle_instance:
        driver_status = "Inactive"
        driver_current_activity = "No Vehicle Assigned"
        
    attendance_instance = await get_tuple_instance(
                        session,
                        DriverAttendance,
                        {'driver_uuid': driver_uuid},
                        extra_conditions=[
                            func.DATE(convert_utc_to_ist(DriverAttendance.attendance_trigger_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
                        ],
                        order_by=[desc(DriverAttendance.id)],
                        limit=1  
                    )
    if attendance_instance:
        driver_status = attendance_states_dict[attendance_instance.attendance_state_uuid]
    
    match driver_status:
        case "Present":
            if attendance_instance.bluetooth_connection_time:
                driver_current_activity = "Vehicle connected"
                porter_trip_instance = await get_tuple_instance(session ,
                                                                AvaronnPorterTrip ,
                                                                {"driver_uuid" : driver_uuid} ,
                                                                 extra_conditions=[
                                                                func.DATE(convert_utc_to_ist(AvaronnPorterTrip.trip_on_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
                                                                ],
                                                                order_by=[desc(AvaronnPorterTrip.id)] ,
                                                                limit = 1)
                if porter_trip_instance:
                    if not porter_trip_instance.trip_off_time:
                        driver_current_activity = "On Trip"
                    else:
                        driver_current_activity = "waiting on drop location"
                hotspot_instance = await get_tuple_instance(session , HotspotRoutes ,{"driver_uuid" : driver_uuid} , order_by=[desc(HotspotRoutes.id)] , limit = 1)
                if hotspot_instance:
                    if hotspot_instance.reached_hotspot:
                        if not hotspot_instance.got_trip:
                            driver_current_activity = "Waiting on hotspot"
                    else:
                        driver_current_activity = "Moving to a hotspot"
            else:
                driver_current_activity = "Marked Present"
        case "Absent":
            driver_current_activity = "Marked absent"
        case "No action":
            driver_current_activity = "Awaiting attendance"
        case "Expired":
            driver_current_activity = "Attendance expired."
        case _:
            driver_current_activity = "Driver on Leave"
        
    return [driver_status , driver_current_activity]



# async def get_ignition_time_sec_and_km(session , vehicle_number , start_timestamp , end_timestamp):
#     query = '''
#             WITH distance AS (
#             SELECT MAX(odometer) - MIN(odometer) AS odometer_travelled
#             FROM vehicle_location
#             WHERE 
#                 created_at BETWEEN :start_timestamp AND :end_timestamp
#                 AND vehicle_number = :vehicle_number
#         ),
#         ignition_time AS (
#             SELECT 
#                 COALESCE(SUM(ignition_duration), 0) AS total_ignition_on_seconds
#             FROM (
#                 SELECT
#                     vehicle_number,
#                     EXTRACT(EPOCH FROM (LEAD(created_at) OVER (PARTITION BY vehicle_number ORDER BY created_at) - created_at)) AS ignition_duration
#                 FROM 
#                     vehicle_location
#                 WHERE 
#                     created_at BETWEEN :start_timestamp AND :end_timestamp
#                     AND ignstatus IN ('on', 'ON')
#             ) AS durations
#             WHERE ignition_duration IS NOT NULL AND
#                 vehicle_number = :vehicle_number
#         )
#         SELECT 
#             COALESCE(distance.odometer_travelled, 0) AS odometer_travelled,
#             ignition_time.total_ignition_on_seconds
#         FROM 
#             distance, ignition_time;
#     '''
#     result = await session.execute(text(query),
#                                    [
#                 {
#                     "vehicle_number":vehicle_number,
#                     "start_timestamp": start_timestamp,
#                     "end_timestamp": end_timestamp
#                 }
#             ]  )
#     rows = result.all()
#     columns = ["distance" , "ignition_time"]
#     data = [dict(zip(columns, row)) for row in rows]
#     return data[0]

