from sqlalchemy import desc
from db.database_operations import get_tuple_instance, insert_into_table
from models.attendace_models import DriverWorkingPolicy, DriverApprovedLeaves, DriverApprovedOffDayWorks, DriverAttendanceSummary, DriverPolicy
from utils.leave_management_utils import get_monthly_required_working_days
from utils.time_utils import get_utc_time
from datetime import datetime


async def driver_working_day(session  , driver_uuid , mfo_uuid):
    working_policy = await get_tuple_instance(session , DriverWorkingPolicy  , {"driver_uuid" : driver_uuid , "mfo_uuid" : mfo_uuid , "valid_till" : None} , order_by=[desc(DriverWorkingPolicy.id)] , limit = 1)
    driver_policy = await get_tuple_instance(session , DriverPolicy  , {"driver_policy_uuid" : working_policy.driver_policy_uuid} , order_by=[desc(DriverPolicy.id)] , limit = 1)

    today_working = datetime.today().strftime('%A').lower() + "_working"
    is_working_today = getattr(driver_policy, today_working, False)
    
    return is_working_today



async def driver_on_leave(session , driver_uuid):
    approved_leave = await get_tuple_instance(session , DriverApprovedLeaves  , {"driver_uuid" : driver_uuid , "leave_date" : get_utc_time().date()})
    if approved_leave:
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
                driver_attendance_summary_instance.total_leave_days +=1
        
        else:
            required_working_days = await get_monthly_required_working_days(session , driver_uuid , year , month)
            next_month_data = {
                    "driver_uuid": driver_uuid, 
                    "year" : year ,
                    "month" : month,
                    "total_leave_days" : 1,
                    "required_working_days" :required_working_days
                }
            
            await insert_into_table(session , DriverAttendanceSummary ,next_month_data)
        
        return True 
    return False
    
    
    

async def driver_on_extra_day_work(session  , driver_uuid):
    extra_work_day = await get_tuple_instance(session , DriverApprovedOffDayWorks  , {"driver_uuid" : driver_uuid , "work_date" : get_utc_time().date()})
    if extra_work_day:
        return True
    return False


