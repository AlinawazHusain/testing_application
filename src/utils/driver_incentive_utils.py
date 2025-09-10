from db.database_operations import get_tuple_instance, insert_into_table
from models.incentive_models import DailyDriverIncentive, DriverDailyTasks, MonthlyDriverIncentive
from settings.static_data_settings import static_table_settings
from sqlalchemy.ext.asyncio import AsyncSession

from utils.time_utils import get_utc_time

async def get_incentive_points(session:AsyncSession, driver_uuid:str , vehicle_uuid:str , mfo_uuid:str, event:str , new_incentive_km:float = 0 ):
    task_type_dict = static_table_settings.static_table_data["TASK_TYPES"]
    task_type_uuid = next((k for k, v in task_type_dict.items() if v["task_type"] == event), None)
    new_incentive_earning = 0
    task_dict = task_type_dict.get(task_type_uuid , None)
    
    points_earned = task_dict["points"] if task_dict else 0
    
    daily_task_data = {
        "mfo_uuid" : mfo_uuid,
        "vehicle_uuid" : vehicle_uuid,
        "driver_uuid" : driver_uuid,
        "task_type_uuid" : task_type_uuid,
        "points_earned" : points_earned,
        "completed_at" : get_utc_time()
    }
    
    session.add(DriverDailyTasks(**daily_task_data))
    
    
    
    driver_daily_incentives_instance = await get_tuple_instance(session , DailyDriverIncentive , {"driver_uuid" : driver_uuid ,  "trip_date" : get_utc_time().date()})
    if driver_daily_incentives_instance:
        curr_points = driver_daily_incentives_instance.daily_tasks_points
        curr_total_points = driver_daily_incentives_instance.daily_task_points_created
        incentive_unlock_percentage = ((curr_points + points_earned) / (curr_total_points + points_earned))*100
        
        driver_daily_incentives_instance.daily_tasks_points = curr_points + points_earned 
        driver_daily_incentives_instance.daily_task_points_created = curr_total_points + points_earned
        driver_daily_incentives_instance.incentive_unlock_percentage = incentive_unlock_percentage
        
        revenue_km = driver_daily_incentives_instance.revenue_km + new_incentive_km
        incentive_earning =  driver_daily_incentives_instance.incentive_earning 
        today = get_utc_time()
        month = today.month
        year = today.year
        monthly_incentive_instance = await get_tuple_instance(session , MonthlyDriverIncentive , {"driver_uuid" : driver_uuid , "month" : month  , "year" : year})
        
        if monthly_incentive_instance:
            if monthly_incentive_instance.total_revenue_km  > 1500:
                new_incentive_earning = new_incentive_km*2.0
                incentive_earning += new_incentive_earning
            elif monthly_incentive_instance.total_revenue_km + driver_daily_incentives_instance.revenue_km + new_incentive_km  > 1500:
                more_than_threshold_km = min(monthly_incentive_instance.total_revenue_km + driver_daily_incentives_instance.revenue_km + new_incentive_km - 1500 , new_incentive_km)
                less_than_threshold_km = new_incentive_km - more_than_threshold_km
                new_incentive_earning = (less_than_threshold_km*1.5) + (more_than_threshold_km *2.0)
                incentive_earning = incentive_earning +  new_incentive_earning
            else:
                new_incentive_earning = new_incentive_km*1.5
                incentive_earning += new_incentive_earning
                
                
        else:
            new_incentive_earning = new_incentive_km*1.5
            incentive_earning += new_incentive_earning
            
        driver_daily_incentives_instance.revenue_km = revenue_km
        driver_daily_incentives_instance.incentive_earning  = incentive_earning
        driver_daily_incentives_instance.final_incentive = (incentive_unlock_percentage/100) * incentive_earning
        
    else:
        incentive_data = {
            "driver_uuid" : driver_uuid,
            "mfo_uuid" : mfo_uuid,
            "vehicle_uuid" :vehicle_uuid,
            "trip_date" : get_utc_time().date(),
            "daily_tasks_points" : points_earned,
            "daily_task_points_created" : points_earned,
            "incentive_unlock_percentage" :  100.0,
            "final_incentive" :0.0
        }
        await insert_into_table(session , DailyDriverIncentive , incentive_data)
        
    if event == "Trip off":
        return points_earned , new_incentive_earning
    else:
        return points_earned



async def get_points_to_earn_on_task(event:str):
    task_type_dict = static_table_settings.static_table_data["TASK_TYPES"]
    task_type_uuid = next((k for k, v in task_type_dict.items() if v["task_type"] == event), None)
    
    task_dict = task_type_dict.get(task_type_uuid , None)
    
    points_to_earn = task_dict["points"] if task_dict else 0
    
    return points_to_earn





# async def add_requested_hotspot_points(session:AsyncSession, driver_uuid:str , vehicle_uuid:str , mfo_uuid:str):
#     pass


# async def add_reached_hotspot_points(session:AsyncSession, driver_uuid:str , vehicle_uuid:str , mfo_uuid:str):
#     pass