import asyncio
import pandas as pd
from sqlalchemy import desc, func, insert, select
from config.exceptions import ForbiddenError
from models.incentive_models import DailyDriverIncentive, MonthlyDriverIncentive
from models.porter_models import  PorterDriverPerformance , PorterPnL , AvaronnPorterTrip
from models.vehicle_models import VehicleMain, VehicleUtilization 
from models.driver_models import DriverMain
from sqlalchemy.ext.asyncio import AsyncSession 
from db.database_operations import get_tuple_instance, insert_into_table
from datetime import date, datetime, time, timedelta
from sqlalchemy import between
from integrations.location_service import get_distance , get_lat_lng
import numpy as np
import re

from utils.time_utils import get_utc_time

def clean_data(value):
    """
    Cleans individual data value by replacing NaN with None.

    Args:
        value (any): Value to be cleaned.

    Returns:
        any: Original value or None if value is NaN.
    """
    
    if isinstance(value, float) and np.isnan(value):
        return None
    return value


def normalize_vehicle_number(vnum: str) -> str:
    if pd.isna(vnum):
        return vnum
    # Remove all dashes
    vnum = vnum.replace('-', '')
    # Match and normalize: e.g. DL01LAQ0023
    match = re.match(r'^([A-Z]{2})0?(\d{1,2})([A-Z]+)(\d{4})$', vnum)
    if match:
        state, rto, series, number = match.groups()
        return f"{state}{int(rto)}{series}{number}"
    return str(vnum)



def convert_time_to_datetime(time_value):
    """
    Converts a `time` object to a full `datetime` by combining with today's date.

    Args:
        time_value (time or datetime): Time value to convert.

    Returns:
        datetime: A datetime object if input is a time, else the original value.
    """

    if isinstance(time_value, time):
        return datetime.combine(date.today(), time_value)
    return time_value  



def convert_ist_to_utc(ist_time: time) -> time:
    """
    Converts IST time to UTC by subtracting 5 hours and 30 minutes.

    Args:
        ist_time (time): Time in IST.

    Returns:
        time: Time converted to UTC.
    """
    
    if ist_time is None or pd.isna(ist_time):  
        return None
    
    ref_date = datetime(2000, 1, 1)  # Any fixed date works
    utc_datetime = datetime.combine(ref_date, ist_time) - timedelta(hours=5, minutes=30)

    return utc_datetime.time()




async def preprocess_order_data(df: pd.DataFrame):
    """
    Preprocesses raw trip/order data, cleaning and formatting datetime and numeric columns.

    Args:
        df (pd.DataFrame): Raw order data.

    Returns:
        pd.DataFrame: Cleaned and transformed order data.
    """
    
    df.rename(columns={'order_date': 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'], dayfirst=False, errors='coerce')

    time_columns = ['start_time', 'end_time']
    for col in time_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.time
        df[col] = df[col].apply(convert_ist_to_utc)
        df[col] = convert_time_to_datetime(df[col])
        

    df['driver_mobile'] = df['driver_mobile'].astype(str)
    # df['vehicle_number'] = df['vehicle_number'].str.replace('-', '', regex=True)
    df['vehicle_number'] = df['vehicle_number'].apply(normalize_vehicle_number)



    charge_columns = [
        'cash_collected', 'waypoint_charge', 'toll', 'overnight_charge' ,
        'trip_fare' , 'commission' , 'earnings' , 'wallet_transaction' ,
        'labor_charge' , 'pickup_extra_charge' , 
        'drop_extra_charge' 
    ]

    df[charge_columns] = df[charge_columns].astype(float)
    df = df.where(pd.notna(df), None)
    return df



    
    
async def preprocess_driver_data(df:pd.DataFrame):
    """
    Preprocesses raw driver login/performance data.

    Args:
        df (pd.DataFrame): Raw driver data.

    Returns:
        pd.DataFrame: Cleaned and transformed driver data.
    """
    
    
    df.rename(columns={'Date': 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'], dayfirst=False, errors='coerce')

    time_columns = ['first_recorded_login_time', 'last_recorded_login_time']
    for col in time_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.time
        df[col] = df[col].apply(convert_ist_to_utc)
        df[col] = convert_time_to_datetime(df[col])
        

    df['driver_mobile'] = df['driver_mobile'].astype(str)

    # df['vehicle_number'] = df['vehicle_number'].str.replace('-', '', regex=True)
    df['vehicle_number'] = df['vehicle_number'].apply(normalize_vehicle_number)
    

    charge_columns = [
        'trip_fare', 'helper_charges', 'toll_charges' ,'dryrun_incentives' , 'trip_incentives',
        'time_spent_idle_in_hrs' , 'time_spent_on_orders_in_hrs',
        'total_login_time_in_hrs' , 'pct_time_utilized' , 'total_business_login_time_in_hrs' , 
        'distance_travelled_during_order_in_kms','distance_travelled_while_idle_in_kms', 
        'total_distance_in_kms','login_incentives', 'mbg_incentives', 'manual_adjustments',
        'withdrawals','trip_fare_components', 'commission', 'cash_collected','wallet_transactions'
    ]
    df[charge_columns] = df[charge_columns].apply(pd.to_numeric, errors='coerce')
    df = df.where(pd.notna(df), None)
    return df




async def process_trip_data(row):
    """
    Fetches geolocation and travel distance/duration for a single trip row.

    Args:
        row (pd.Series): A single trip record.

    Returns:
        pd.Series: Processed data with coordinates and travel info.
    """
    
    distance, duration = None, None 
    
    pickup_coordinates = await get_lat_lng(row["pickup_address"])
    drop_coordinates = await get_lat_lng(row["drop_address"])
    
    if pickup_coordinates and drop_coordinates:
        distance_and_duration = await get_distance(
            f"{pickup_coordinates[0]},{pickup_coordinates[1]}", f"{drop_coordinates[0]},{drop_coordinates[1]}"
        )
        if distance_and_duration:
            distance = distance_and_duration[0]
            duration = (datetime.min + timedelta(minutes=distance_and_duration[1])).time() if distance_and_duration[1] else None
    return pd.Series({
        "pickup_lat": pickup_coordinates[0] if pickup_coordinates else None,
        "pickup_lng": pickup_coordinates[1] if pickup_coordinates else None,
        "drop_lat": drop_coordinates[0] if drop_coordinates else None,
        "drop_lng": drop_coordinates[1] if drop_coordinates else None,
        "distance_km": distance,
        "duration_min": duration
    })
    
    
    
    
    
async def upload_driver_performance(session:AsyncSession , vehicle_mapping , driver_mapping , full_day_data):
    """
    Inserts driver performance data into the database.

    Args:
        session (AsyncSession): Database session.
        vehicle_mapping (dict): Mapping of vehicle_number to UUID.
        driver_mapping (dict): Mapping of driver_mobile to UUID.
        full_day_data (pd.DataFrame): Processed full-day driver data.
    """
    
    try:
    
        performance_records = []

        for _, row in full_day_data.iterrows():
            vehicle_uuid = vehicle_mapping.get(row['vehicle_number'], None)
            driver_uuid = driver_mapping.get(row['driver_mobile'], None)
            
            performance_records.append({
                'date': row['date'],
                'driver_uuid': driver_uuid,
                'vehicle_uuid': vehicle_uuid,
                'total_login_time_hrs': clean_data(row['total_login_time_in_hrs']),
                'idle_time_hrs': clean_data(row['time_spent_idle_in_hrs']),
                'time_spent_on_orders_in_hrs': clean_data(row['total_login_time_in_hrs']),
                'distance_in_order_km': clean_data(row['distance_travelled_during_order_in_kms']),
                'distance_in_idle_km': clean_data(row['distance_travelled_while_idle_in_kms']),
                'total_distance_km': clean_data(row['total_distance_in_kms']),
                'notifications_received': clean_data(row['total_notifs_overall']),
                'notification_accepeted': clean_data(row['accept_notifs_overall']),
                'acceptance_rate_pct': clean_data(100.0 - row['pct_notifs_missed_overall']),
                'utilizaion_pct': clean_data(row['pct_time_utilized']),
                'first_login_time': datetime.combine(row['date'], row['first_recorded_login_time']) if pd.notna(row['first_recorded_login_time']) else None,
                'last_logout_time': datetime.combine(row['date'], row['last_recorded_login_time']) if pd.notna(row['last_recorded_login_time']) else None,
                'first_cluster': row['first_location_in_cluster'],
                'last_cluster': row['last_location_in_cluster']
            })

        if performance_records:
            await session.execute(insert(PorterDriverPerformance), performance_records)
            await session.commit()

    except Exception as e:
        print(str(e))
            
    

            
            
            

async def upload_porter_pnl(session:AsyncSession , vehicle_mapping , driver_mapping , trip_wise_data):
    """
    Inserts Porter PnL (Profit and Loss) data for each completed trip.

    Args:
        session (AsyncSession): Database session.
        vehicle_mapping (dict): Mapping of vehicle_number to UUID.
        driver_mapping (dict): Mapping of driver_mobile to UUID.
        trip_wise_data (pd.DataFrame): Processed trip data.
    """
    
    porter_pnl_records = []
    try:
        for i in range(len(trip_wise_data)):
            vehicle_uuid = vehicle_mapping.get(trip_wise_data.iloc[i]['vehicle_number'] , None)
            driver_uuid = driver_mapping.get(trip_wise_data.iloc[i]['driver_mobile']  , None)
            if trip_wise_data.iloc[i]['status'] == 'completed':
                start_time = trip_wise_data.iloc[i]['start_time']
                end_time = trip_wise_data.iloc[i]['end_time']
                date = trip_wise_data.iloc[i]['date']

                if pd.notna(start_time) and pd.notna(end_time):
                    start_datetime = datetime.combine(date, start_time)
                    end_datetime = datetime.combine(date, end_time)
                    
                    time_taken_seconds = (end_datetime - start_datetime).total_seconds()
                    
                    # Convert seconds to HH:MM:SS time format
                    hours, remainder = divmod(int(time_taken_seconds), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    time_taken = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                else:
                    time_taken = None     
                trip_date = trip_wise_data.iloc[i]['date']
                trip_start_time = trip_wise_data.iloc[i]['start_time']

                if pd.notna(trip_start_time):
                    trip_start_datetime = datetime.combine(trip_date, trip_start_time)
                    
                    start_range = trip_start_datetime - timedelta(minutes=20)
                    end_range = trip_start_datetime + timedelta(minutes=20)
                else:
                    start_range = None
                    end_range = None
                extra_conditions = None
                if start_range and end_range:
                    extra_conditions = [
                        between(AvaronnPorterTrip.trip_on_time, start_range, end_range)
                    ]
                avaronn_porter_trip_instance = await get_tuple_instance(
                    session, AvaronnPorterTrip, 
                    {'vehicle_uuid': vehicle_uuid, 'driver_uuid': driver_uuid}, 
                    extra_conditions=extra_conditions,
                    order_by=[desc(AvaronnPorterTrip.id)],
                    limit = 1
                )
                avaronn_porter_trip_uuid = avaronn_porter_trip_instance.avaronn_porter_trip_uuid if avaronn_porter_trip_instance else ''
                porter_pnl_records.append({
                'date' : date,
                'driver_uuid' : driver_uuid,
                'vehicle_uuid' : vehicle_uuid,
                'trip_fare' : trip_wise_data.iloc[i]['trip_fare'] ,
                'avaronn_porter_trip_uuid' : avaronn_porter_trip_uuid,
                'porter_order_id' : trip_wise_data.iloc[i]['crn_order_id'],
                'trip_earnings' : trip_wise_data.iloc[i]['earnings'],
                'trip_commission' : trip_wise_data.iloc[i]['commission'],
                'trip_status' : trip_wise_data.iloc[i]['status'],
                'wallet_transaction' : trip_wise_data.iloc[i]['wallet_transaction'],
                'trip_start_time' : start_datetime if pd.notna(start_time) else None,
                'trip_end_time' :end_datetime if pd.notna(end_time) else None,
                "pickup_lat" : trip_wise_data.iloc[i]['pickup_lat'],
                "pickup_lng": trip_wise_data.iloc[i]['pickup_lng'],
                "drop_lat" : trip_wise_data.iloc[i]['drop_lat'],
                "drop_lng": trip_wise_data.iloc[i]['drop_lng'],
                "distance_km": trip_wise_data.iloc[i]['distance_km'],
                "duration_min": trip_wise_data.iloc[i]['duration_min']
            })
        if porter_pnl_records:
                await session.execute(insert(PorterPnL), porter_pnl_records)
    except Exception as e:
        print(e)
        raise e
            
            
            
            

async def upload_driver_incentive(session:AsyncSession ,driver_mapping  ,full_day_data ):
    """
    Inserts Porter PnL (Profit and Loss) data for each completed trip.

    Args:
        session (AsyncSession): Database session.
        vehicle_mapping (dict): Mapping of vehicle_number to UUID.
        driver_mapping (dict): Mapping of driver_mobile to UUID.
        trip_wise_data (pd.DataFrame): Processed trip data.
    """
    try:
        for i in range(len(full_day_data)):
            driver_uuid = driver_mapping.get(full_day_data.iloc[i]['driver_mobile']  , None)
            
            distance_km = clean_data(full_day_data.iloc[i]['distance_travelled_during_order_in_kms'])
            trip_date = full_day_data.iloc[i]['date']
            trip_date_only = trip_date.date() 
            driver_daily_incenctive_instance  = await get_tuple_instance(session ,
                                                                        DailyDriverIncentive ,
                                                                        {"driver_uuid" : driver_uuid },
                                                                        extra_conditions=[
                                                                            func.DATE(DailyDriverIncentive.trip_date) == func.DATE(trip_date_only)
                                                                        ])

            if driver_daily_incenctive_instance:
                incentive_unlock_percentage = driver_daily_incenctive_instance.incentive_unlock_percentage
                driver_daily_incenctive_instance.revenue_km = distance_km
                
                incentive_earning = 0
                
                
                month = trip_date.month
                year = trip_date.year
                monthly_incentive_instance = await get_tuple_instance(session , MonthlyDriverIncentive , {"driver_uuid" : driver_uuid , "month" : month  , "year" : year})
                if monthly_incentive_instance:
                    if monthly_incentive_instance.total_revenue_km  > 1500:
                        new_incentive_earning = distance_km*2.0
                        incentive_earning = new_incentive_earning
                    elif monthly_incentive_instance.total_revenue_km + distance_km > 1500:
                        more_than_threshold_km = min(monthly_incentive_instance.total_revenue_km + distance_km - 1500 , distance_km)
                        less_than_threshold_km = distance_km - more_than_threshold_km
                        new_incentive_earning = (less_than_threshold_km*1.5) + (more_than_threshold_km *2.0)
                        incentive_earning = incentive_earning +  new_incentive_earning
                    else:
                        new_incentive_earning = distance_km*1.5
                        incentive_earning = new_incentive_earning
                        
                        
                else:
                    new_incentive_earning = distance_km*1.5
                    incentive_earning = new_incentive_earning
                    
                driver_daily_incenctive_instance.incentive_earning  = incentive_earning
                final_incentive = (incentive_unlock_percentage/100) * incentive_earning
                driver_daily_incenctive_instance.final_incentive = final_incentive
                

                if monthly_incentive_instance:
                    monthly_incentive_instance.points_earned += driver_daily_incenctive_instance.daily_tasks_points
                    monthly_incentive_instance.total_points += driver_daily_incenctive_instance.daily_task_points_created
                    monthly_incentive_instance.total_incentive += incentive_earning
                    monthly_incentive_instance.total_incentive_earned += final_incentive
                
                
                else:
                    monthly_incentive_data = {
                        "driver_uuid" : driver_uuid,
                        "month_start" : get_utc_time().date(),
                        "month" : month,
                        "year" :year,
                        "points_earned" : driver_daily_incenctive_instance.daily_tasks_points,
                        "total_points" : driver_daily_incenctive_instance.daily_task_points_created,
                        "total_revenue_km" : distance_km,
                        "base_km" : distance_km,
                        "base_rate" : 1.5,
                        "bonus_rate" : 2.0,
                        "base_incentive" : final_incentive,
                        "total_incentive_earned" : final_incentive,
                        "total_incentive" : incentive_earning,
                        "total_days_eligible" : 26
                    }
                    await insert_into_table(session , MonthlyDriverIncentive , monthly_incentive_data)
                await session.flush()
    except Exception as e:
        print(str(e))
                

async def upload_vehicle_utilization(session , driver_mapping , vehicle_mapping , full_day_data):
    utilization_records = []

    for _, row in full_day_data.iterrows():
        vehicle_uuid = vehicle_mapping.get(row['vehicle_number'], None)
        if vehicle_uuid:
            driver_uuid = driver_mapping.get(row['driver_mobile'], None)
            
            utilization_records.append({
                'date': row['date'],
                'driver_uuid': driver_uuid,
                'vehicle_uuid': vehicle_uuid,
                'total_hours': clean_data(row['total_login_time_in_hrs']),
                'onspot_hours': clean_data(row['total_login_time_in_hrs']),
                "schedule_hours" : 0.0,
                'order_kms': clean_data(row['distance_travelled_during_order_in_kms']),
                'ideal_kms': clean_data(row['distance_travelled_while_idle_in_kms']),
                'total_distance_km': clean_data(row['total_distance_in_kms']),
                'utilization_score': clean_data(row['pct_time_utilized']),
            })

    if utilization_records:
        await session.execute(insert(VehicleUtilization), utilization_records)
        await session.commit()


            
            
            


async def porter_data_handler(session: AsyncSession , order_data , driver_data):
    
    """
    Handles the full data ingestion pipeline:
    - Preprocesses trip and driver data
    - Validates date consistency
    - Processes geolocation and time
    - Inserts driver performance, hotspot, and PnL data

    Args:
        session (AsyncSession): Database session.
        order_data (pd.DataFrame): Raw Porter trip data.
        driver_data (pd.DataFrame): Raw Porter driver login and performance data.

    Raises:
        ForbiddenError: If data is inconsistent or not from the same date.
    """
    
    
    try:
        trip_wise_data, full_day_data = await asyncio.gather(
            preprocess_order_data(order_data),
            preprocess_driver_data(driver_data)
        )
    # yesterday_date = (get_utc_time() - timedelta(days=1)).date()
  
        if trip_wise_data.iloc[0]['date'].date() == full_day_data.iloc[0]['date'].date():
        # 3. Extract unique values
            all_vehicle_numbers = full_day_data['vehicle_number'].unique().tolist()
            all_driver_mobiles = full_day_data['driver_mobile'].unique().tolist()

            # 4. Process trip data asynchronously
            processed_trip_data = await asyncio.gather(
                *[process_trip_data(row) for _, row in trip_wise_data.iterrows()]
            )
            trip_wise_data[["pickup_lat", "pickup_lng", "drop_lat", "drop_lng", "distance_km", "duration_min"]] = processed_trip_data

            # 5. Fetch vehicle & driver mappings in parallel
            vehicle_query = select(
                VehicleMain.vehicle_number,
                VehicleMain.vehicle_uuid,
                VehicleMain.is_enable
            ).where(
                VehicleMain.vehicle_number.in_(all_vehicle_numbers)
            )

            driver_query = select(
                DriverMain.phone_number,
                DriverMain.driver_uuid,
                DriverMain.is_enable
            ).where(
                DriverMain.phone_number.in_(all_driver_mobiles)
            )

            # Run both queries concurrently
            # vehicle_records, driver_records = await asyncio.gather(
            #     session.execute(vehicle_query),
            #     session.execute(driver_query)
            # )
            vehicle_records = await session.execute(vehicle_query)
            driver_records = await session.execute(driver_query)

            # Convert results to mappings (dict-like rows)
            vehicle_rows = vehicle_records.mappings().all()
            driver_rows = driver_records.mappings().all()

            # Build mappings only for enabled records
            vehicle_mapping = {
                row["vehicle_number"]: row["vehicle_uuid"]
                for row in vehicle_rows
            }

            driver_mapping = {
                row["phone_number"]: row["driver_uuid"]
                for row in driver_rows
            }

            # 6. Run data insertions concurrently
            # await asyncio.gather(
            print("done1")
            await upload_driver_performance(session, vehicle_mapping, driver_mapping, full_day_data)
            print("done2")
            await upload_porter_pnl(session, vehicle_mapping, driver_mapping, trip_wise_data)
            print("done3")
            await upload_driver_incentive(session , driver_mapping , full_day_data)
            print("done4")
            await upload_vehicle_utilization(session , driver_mapping , vehicle_mapping , full_day_data)
            print("done5")
            # )
            await session.commit()
        else:
            raise ForbiddenError("Data is not of same date")
    
    except ForbiddenError as e:
        raise e
    
    except Exception as e:
        raise ForbiddenError("Inconsistant or Incorrect Data")

