# from geoalchemy2.shape import from_shape
# from shapely.geometry import Point
# import pandas as pd
# from datetime import date, datetime, time, timedelta
# import numpy as np

# from models.hotspot_routes_models import HotspotData

# def clean_data(value):
#     """
#     Cleans individual data value by replacing NaN with None.

#     Args:
#         value (any): Value to be cleaned.

#     Returns:
#         any: Original value or None if value is NaN.
#     """
    
#     if isinstance(value, float) and np.isnan(value):
#         return None
#     return value



# def convert_time_to_datetime(time_value):
#     """
#     Converts a `time` object to a full `datetime` by combining with today's date.

#     Args:
#         time_value (time or datetime): Time value to convert.

#     Returns:
#         datetime: A datetime object if input is a time, else the original value.
#     """

#     if isinstance(time_value, time):
#         return datetime.combine(date.today(), time_value)
#     return time_value  

# def convert_ist_to_utc(ist_time: time) -> time:
#     """
#     Converts IST time to UTC by subtracting 5 hours and 30 minutes.

#     Args:
#         ist_time (time): Time in IST.

#     Returns:
#         time: Time converted to UTC.
#     """
    
#     if ist_time is None or pd.isna(ist_time):  
#         return None
    
#     ref_date = datetime(2000, 1, 1)  # Any fixed date works
#     utc_datetime = datetime.combine(ref_date, ist_time) - timedelta(hours=5, minutes=30)

#     return utc_datetime.time()




# async def preprocess_order_data(df: pd.DataFrame):
#     """
#     Preprocesses raw trip/order data, cleaning and formatting datetime and numeric columns.

#     Args:
#         df (pd.DataFrame): Raw order data.

#     Returns:
#         pd.DataFrame: Cleaned and transformed order data.
#     """
    
#     df.rename(columns={'order_date': 'date'}, inplace=True)
#     df['date'] = pd.to_datetime(df['date'], dayfirst=False, errors='coerce')

#     time_columns = ['start_time', 'end_time']
#     for col in time_columns:
#         # df[col] = pd.to_datetime(df[col], errors='coerce').dt.time
#         # df[col] = df[col].apply(convert_ist_to_utc)
#         # df[col] = convert_time_to_datetime(df[col])
#         df[col] = pd.to_datetime(df[col], errors='coerce').dt.time
#         df[col] = df[col].apply(convert_ist_to_utc)
#         df[col] = df[col].apply(convert_time_to_datetime)
        

#     df['driver_mobile'] = df['driver_mobile'].astype(str)
#     df['vehicle_number'] = df['vehicle_number'].str.replace('-', '', regex=True)


#     charge_columns = [
#         'cash_collected', 'waypoint_charge', 'toll', 'overnight_charge' ,
#         'trip_fare' , 'commission' , 'earnings' , 'wallet_transaction' ,
#         'labor_charge' , 'pickup_extra_charge' , 
#         'drop_extra_charge' 
#     ]

#     df[charge_columns] = df[charge_columns].astype(float)
#     df = df.where(pd.notna(df), None)
#     return df




# def create_point_if_valid(lat, lon):
#     if pd.isna(lat) or pd.isna(lon):
#         return None
#     return from_shape(Point(lon, lat), srid=4326)  # Note: (lon, lat)



# async def push_porter_processed_data_into_db(session):
#     print("reading csv...")
#     df = pd.read_csv("static/merged_orders_combined_final.csv")
#     print("start preprocessing..")
#     df = await preprocess_order_data(df)
#     df = df.replace({np.nan: None})
#     print("preprocessing done..")
#     df["pickup_location"] = df.apply(lambda row: create_point_if_valid(row["pickup_lat"], row["pickup_long"]), axis=1)
#     df["drop_location"] = df.apply(lambda row: create_point_if_valid(row["drop_lat"], row["drop_long"]), axis=1)
#     print("posgis columns added..")
    
#     final_df = df[[ "driver_geo_region" , "pickup_address"  , "drop_address"  , "start_time" , "end_time"  , "status" , "drop_lat" , "drop_long" , "pickup_lat" , "pickup_long" , "pickup_location" , "drop_location" ]]
#     # Assuming 'pickup_location' and 'drop_location' are the WKB columns
#     final_df.to_csv("final_data.csv")
#     print("data preprocessed ...")
#     batch = []
#     for i in range(len(final_df)):
#         batch.append({
#             "driver_geo_region" : final_df.iloc[i]["driver_geo_region"],
#             "pickup_address"  : final_df.iloc[i]["pickup_address"],
#             "drop_address"  : final_df.iloc[i]["drop_address"],
#             "start_time" : final_df.iloc[i]["start_time"],
#             "end_time"  : final_df.iloc[i]["end_time"],
#             "status" : final_df.iloc[i]["status"],
#             "drop_lat" : final_df.iloc[i]["drop_lat"],
#             "drop_long" : final_df.iloc[i]["drop_long"],
#             "pickup_lat" : final_df.iloc[i]["pickup_lat"],
#             "pickup_long" : final_df.iloc[i]["pickup_long"],
#             "pickup_location": final_df.iloc[i]["pickup_location"],
#             "drop_location" :final_df.iloc[i]["drop_location"]
#         })
        
#         if len(batch) >= 5000:
#                     await session.execute(HotspotData.__table__.insert(), batch)
#                     await session.commit()
#                     batch.clear()
#     if batch:
#         await session.execute(HotspotData.__table__.insert(), batch)
#         await session.commit()
#     # 3. Push data to a table (e.g., 'people')
#     print(f"done")
