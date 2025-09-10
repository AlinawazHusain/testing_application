import calendar
from datetime import datetime

from sqlalchemy import desc

from db.database_operations import get_tuple_instance
from models.attendace_models import DriverWorkingPolicy, DriverPolicy


def get_day_dates(year: int, month: int , day_to_search:str):
    day_to_int = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6
    }
    search_day = day_to_int[day_to_search]
    dates = []
    _, num_days = calendar.monthrange(year, month)
    
    for d in range(1, num_days + 1):
        date_obj = datetime(year, month, d)
        if date_obj.weekday() == search_day:
            dates.append(date_obj.date().day)

    return dates



async def get_off_days(session , driver_policy_uuid , year , month):
    driver_policy_instance = await get_tuple_instance(session , DriverPolicy , {"driver_policy_uuid" : driver_policy_uuid})
    
    week_days = ["monday" , "tuesday" , "wednesday" ,"thursday"  , "friday" ,"saturday"  ,"sunday"]
    off_dates = []
    for day in week_days:
        is_working = getattr(driver_policy_instance, f"{day}_working")
        if not is_working:
            off_day_dates = get_day_dates(year , month , day)
            off_dates.extend(off_day_dates)
    return off_dates



async def get_monthly_required_working_days(session , driver_uuid , year , month):
    working_policy = await get_tuple_instance(session , DriverWorkingPolicy  , {"driver_uuid" : driver_uuid} , order_by=[desc(DriverWorkingPolicy.id)] , limit = 1)
    driver_policy = await get_tuple_instance(session , DriverPolicy  , {"driver_policy_uuid" : working_policy.driver_policy_uuid} , order_by=[desc(DriverPolicy.id)] , limit = 1)
    
    working_days = 0
    week_days = ["monday" , "tuesday" , "wednesday" ,"thursday"  , "friday" ,"saturday"  ,"sunday"]
    working_dates = []
    for day in week_days:
        is_working = getattr(driver_policy, f"{day}_working")
        if  is_working:
            working_date = get_day_dates(year , month , day)
            working_dates.extend(working_date)
    
    working_days = len(working_dates)
    
    return working_days
    
