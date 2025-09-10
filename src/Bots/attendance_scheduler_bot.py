from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, time
from db.database_operations import fetch_from_table, get_tuple_instance, insert_into_table
from helpers.mfo_helpers.mfo_driver_helper import create_driver_policy
from models.assignment_mapping_models import DriverFutureArrangement, MfoVehicleMapping
from models.attendace_models import DriverAttendance, DriverWorkingPolicy
from models.vehicle_models import VehicleMain
from utils.time_utils import get_utc_time
from sqlalchemy.exc import SQLAlchemyError
from config.exceptions import DatabaseError
from settings.static_data_settings import static_table_settings
from utils.attendance_utils import driver_on_extra_day_work, driver_on_leave, driver_working_day


BATCH_SIZE = 5000  

async def attendance_scheduler(session: AsyncSession):
    """
    Duplicates the previous day's driver attendance records into today's records 
    for drivers who were assigned to vehicles and did not take any action. Also updates 
    the vehicle status to 'Inactive'.

    This function performs the following steps:
    1. Queries all Vehicles.
    2. Skip for the vehicles having no currnet assigned driver.
    3. Creates new attendance records for today using the "No action" attendance state and 
       connected time state.
    4. Updates the corresponding vehicle status to "Inactive".
    5. Inserts the new records in batches to optimize performance.

    Args:
        session (AsyncSession): SQLAlchemy async session for performing database operations.

    Returns:
        dict: A dictionary containing a success message with the number of records inserted.

    Raises:
        DatabaseError: If any SQLAlchemy exception occurs during the process.

    Note:
        - The function ensures the session is closed after operation, regardless of success or failure.
        - The batch size for inserts is controlled by the BATCH_SIZE constant.
        
    """

    try:
        vehicle_status_dict = static_table_settings.static_table_data["VEHICLE_STATUS"]
        inactive_status = next((k for k, v in vehicle_status_dict.items() if v == 'Inactive'), None)
        today_date = get_utc_time().date()
        attendance_status_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
        no_action_attendance_status = next((k for k , v in attendance_status_dict.items() if v == "No action") , None)
        
        time_state_status_dict = static_table_settings.static_table_data['DRIVER_VEHICLE_CONNECTED_TIME_STATES']
        no_action_time_state_status = next((k for k , v in time_state_status_dict.items() if v == "No action") , None)
 
        stmt = (
            select(DriverFutureArrangement)
            .distinct(DriverFutureArrangement.vehicle_uuid)
            .order_by(DriverFutureArrangement.vehicle_uuid, desc(DriverFutureArrangement.id))
        )
        result = await session.execute(stmt)
        today_assignments = result.scalars().all()
        
        for today_assignment in today_assignments:
            driver_already_assigned = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : today_assignment.driver_uuid , "is_enable" : True })
            if not driver_already_assigned:
                unique_attribute = {"vehicle_uuid": today_assignment.vehicle_uuid , "is_enable" : True}
                vehicle_main_instance = await get_tuple_instance(session , VehicleMain, unique_attribute)
                if vehicle_main_instance:
                    vehicle_main_instance.assigned = True
                    vehicle_main_instance.driver_uuid = today_assignment.driver_uuid
                
                mfo_vehicle_mapping_instance = await get_tuple_instance(session , MfoVehicleMapping , {"vehicle_uuid": today_assignment.vehicle_uuid , "is_enable" : True})
                
                if mfo_vehicle_mapping_instance:
                    if mfo_vehicle_mapping_instance.current_assigned_driver:
                        assigned_driver_uuid = mfo_vehicle_mapping_instance.current_assigned_driver
                        mfo_vehicle_mapping_instance.is_enable = False
                        mfo_vehicle_mapping_instance.disabled_at = get_utc_time()
                    
                        new_mapping_data = {
                            
                            "vehicle_uuid" : mfo_vehicle_mapping_instance.vehicle_uuid,
                            "mfo_uuid" : mfo_vehicle_mapping_instance.mfo_uuid,
                            
                            "primary_driver" : mfo_vehicle_mapping_instance.primary_driver,
                            "secondary_driver" : mfo_vehicle_mapping_instance.secondary_driver,
                            "tertiary1_driver" : mfo_vehicle_mapping_instance.tertiary1_driver,
                            "tertiary2_driver" : mfo_vehicle_mapping_instance.tertiary2_driver,
                            "supervisor_driver" : mfo_vehicle_mapping_instance.supervisor_driver
                        }
                    
                        await insert_into_table(session , MfoVehicleMapping ,new_mapping_data)

                        driver_working_policy_instance = await get_tuple_instance(session , 
                                                                                DriverWorkingPolicy ,
                                                                                {"driver_uuid" : assigned_driver_uuid , "mfo_uuid" : mfo_vehicle_mapping_instance.mfo_uuid} , 
                                                                                order_by = [desc(DriverWorkingPolicy.id)],
                                                                                limit =1
                                                                                )
                        driver_working_policy_instance.valid_till = get_utc_time()
                
                    else:
                        mfo_vehicle_mapping_instance.current_assigned_driver = today_assignment.driver_uuid
                        await create_driver_policy(session , today_assignment.driver_uuid , mfo_vehicle_mapping_instance.mfo_uuid)
                
    
        await session.commit()
    
        
        mappings = await fetch_from_table(session ,MfoVehicleMapping , None , {"is_enable" : True})
        batch = []
        total_inserted = 0

        for record in mappings:
            if record["current_assigned_driver"]:
            
                extra_day_work = False
                is_working_day = await driver_working_day(session , record["current_assigned_driver"] , record["mfo_uuid"])
                if is_working_day:
                    on_leave = await driver_on_leave(session , record["current_assigned_driver"])
                    if on_leave:
                        continue
                
                else:
                    on_extra_work = await driver_on_extra_day_work(session , record["current_assigned_driver"])
                    if not on_extra_work:
                        continue
                    else:
                        extra_day_work = True
                
                vehicle_main_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : record["vehicle_uuid"] , "is_enable" : True})
                vehicle_main_instance.vehicle_status = inactive_status
                batch.append({
                    "driver_uuid": record["current_assigned_driver"],
                    "vehicle_uuid": record["vehicle_uuid"],
                    "mfo_uuid": record["mfo_uuid"],
                    "attendance_state_uuid" : no_action_attendance_status,
                    "attendance_trigger_time": datetime.combine(today_date,  time(9, 30, 0)),
                    "expected_time_stamp" : time(0, 30, 0),
                    "driver_attendance_vehicle_connected_time_state_uuid" : no_action_time_state_status,
                    "extra_day_work" : extra_day_work
                })
            
            
                if len(batch) >= BATCH_SIZE:
                    await session.execute(DriverAttendance.__table__.insert(), batch)
                    await session.commit()
                    total_inserted += len(batch)
                    batch.clear()
        if batch:
            await session.execute(DriverAttendance.__table__.insert(), batch)
            await session.commit()
            total_inserted += len(batch)
        return {"message": f"Successfully duplicated {total_inserted} attendance records for today"}

    except SQLAlchemyError as e:
        await session.rollback()
        print(e)
        raise DatabaseError(f"Error in updating attendances : {str(e)}")
    
    finally:
        await session.close()
