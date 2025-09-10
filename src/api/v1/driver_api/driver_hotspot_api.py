# from datetime import timedelta
# from fastapi import APIRouter, Depends, Header, Request
# from sqlalchemy import desc, func
# from auth.dependencies import driver_role_required
# from config.exceptions import ForbiddenError
# from db.database_operations import get_tuple_instance
# from db.db import get_async_db
# from helpers.driver_helpers.driver_hotspot_helper import get_route, save_route_to_db
# from models.hotspot_routes_models import HotspotRoutes
# from models.porter_models import AvaronnPorterTrip
# from schemas.v1.driver_schemas.driver_hotspot_schema import get_hotspot_request, get_hotspot_response
# from schemas.v1.standard_schema import standard_success_response
# from sqlalchemy.ext.asyncio import AsyncSession
# from utils.response import success_response
# from settings.static_data_settings import static_table_settings
# from utils.time_utils import get_utc_time


# driver_hotspot_router = APIRouter()





# @driver_hotspot_router.get("/getHotspot" , response_model = standard_success_response[get_hotspot_response])
# async def getHotspot_api(request:Request,
#                                req:get_hotspot_request ,
#                                driver_uuid = Depends(driver_role_required()),
#                                session:AsyncSession = Depends(get_async_db),
#                                session_id: str = Header(..., alias="session-id"),
#                                device_id: str = Header(..., alias="device-id")
#                                ):
#     last_hotspot_instance = await get_tuple_instance(session ,
#                                                      HotspotRoutes,
#                                                      {'driver_uuid': driver_uuid},
#                                                      order_by=[desc(HotspotRoutes.id)],
#                                                      extra_conditions=[
#                                                         func.DATE(HotspotRoutes.created_at) == func.DATE(get_utc_time())
#                                                     ],
#                                                      limit=1 
#                                                      )
#     if last_hotspot_instance:
#         today = get_utc_time()
#         time_of_last_hotspot = abs(today - last_hotspot_instance.created_at)
#         if last_hotspot_instance.reached_hotspot_timestamp:
#             time_of_last_hotspot = abs(today - last_hotspot_instance.reached_hotspot_timestamp )
        
#         if last_hotspot_instance.got_trip:
#             avatonn_porter_trip_instance = await get_tuple_instance(session , AvaronnPorterTrip , {"avaronn_porter_trip_uuid" : last_hotspot_instance.avaronn_porter_trip_uuid})
#             time_of_last_hotspot = abs(today - avatonn_porter_trip_instance.trip_off_time)
        
#         if time_of_last_hotspot < timedelta(minutes=20):
#             remaining_time = timedelta(minutes=20) - time_of_last_hotspot
#             remaining_minutes = int(remaining_time.total_seconds() // 60)
#             raise ForbiddenError(f"{remaining_minutes} mins")
            
#     input_coords = (req.driver_lat, req.driver_lng)

#     cluster_tree = static_table_settings.static_table_data["CLUSTERED_TREE"]
#     cluster_centers = static_table_settings.static_table_data["CLUSTER_CENTERS"]
#     df = static_table_settings.static_table_data["CLUSTED_CSV_DATA"]
    
#     dist, idx = cluster_tree.query([input_coords])
#     nearest_cluster = cluster_centers.iloc[idx[0]]['cluster']
#     min_distance = dist[0]

#     cluster_points = df[df['cluster'] == nearest_cluster]

#     mode_point = cluster_points[['lat', 'long']].mode().iloc[0]

    


#     cluster_dict = {"cluster_id": int(nearest_cluster),
#         "distance_meters": round(min_distance, 2),
#         "most_frequent_point": {
#             "latitude": float(mode_point['lat']),
#             "longitude": float(mode_point['long'])
#         }}

    
#     route = await get_route(input_coords[0],
#                         input_coords[1],
#                         round(cluster_dict['most_frequent_point']['latitude'],5),
#                         round(cluster_dict['most_frequent_point']['longitude'],5)
#                         )

#     hotspot_route_uuid = await save_route_to_db(session , driver_uuid , route)
#     route["hotspot_route_uuid"] = hotspot_route_uuid
#     await session.commit()
#     await session.close()
#     return success_response(request , get_hotspot_response(**route) , "get hotspot successfully" , False)

from datetime import timedelta
from fastapi import APIRouter, Depends, Header, Request
import pandas as pd
from sqlalchemy import desc, func, select
from auth.dependencies import driver_role_required
from config.exceptions import ForbiddenError
from db.database_operations import get_tuple_instance
from db.db import get_async_db
from helpers.driver_helpers.driver_hotspot_helper import get_route, save_route_to_db, find_closest_hotspot, score_nearby_pickups
from models.hotspot_routes_models import HotspotRoutes
from models.porter_models import AvaronnPorterTrip
from schemas.v1.driver_schemas.driver_hotspot_schema import get_hotspot_request, get_hotspot_response
from schemas.v1.standard_schema import standard_success_response
from sqlalchemy.ext.asyncio import AsyncSession
from utils.response import success_response
from utils.time_utils import get_utc_time
from datetime import datetime, timedelta
import time


driver_hotspot_router = APIRouter()
@driver_hotspot_router.get("/getHotspot" , response_model = standard_success_response[get_hotspot_response])
async def getHotspot_api(request:Request,
                               req:get_hotspot_request ,
                               driver_uuid = Depends(driver_role_required()),
                               session:AsyncSession = Depends(get_async_db),
                               session_id: str = Header(..., alias="session-id"),
                               device_id: str = Header(..., alias="device-id")
                               ):
    # driver_uuid = 'DR-3'  # For testing purposes, replace with actual driver_uuid from auth dependency
    last_hotspot_instance = await get_tuple_instance(session ,
                                                     HotspotRoutes,
                                                     {'driver_uuid': driver_uuid},
                                                     order_by=[desc(HotspotRoutes.id)],
                                                     extra_conditions=[
                                                        func.DATE(HotspotRoutes.created_at) == func.DATE(get_utc_time())
                                                    ],
                                                     limit=1
                                                     )

    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    start_time = one_hour_ago


    stmt = select(HotspotRoutes).where(
        # HotspotRoutes.created_at >= start_time
    )



    # Execute
    result = await session.execute(stmt)
    rows = result.scalars().all()
    # for row in rows:
    #     if row.crn_order_id is not None:
    #         print(f"CRN Order ID: {row.crn_order_id}, Created At: {row.created_at}, Got Trip: {row.got_trip}, Reached Hotspot: {row.reached_hotspot_timestamp}")
    crn_order_id_occupied = [row.crn_order_id for row in rows if row.crn_order_id is not None and row.created_at >= start_time]

    rows_df = pd.DataFrame(
    [(r.crn_order_id, r.got_trip) for r in rows if r.crn_order_id is not None],
    columns=["crn_order_id", "got_trip"]
)

    # Group and calculate sum (True is 1, False is 0)
    agg_df = rows_df.groupby("crn_order_id").agg(
    got_trip_sum_true=("got_trip", "sum"),              # sums True as 1, False as 0
    got_trip_sum_false=("got_trip", lambda x: (~x).sum())  # counts False values by negating the boolean series
    ).reset_index()


    start_time = time.time()
    input_coords = (req.driver_lat, req.driver_lng)
    current_hour = get_utc_time().hour
    current_day_of_week = get_utc_time().weekday()
    current_time= get_utc_time() + timedelta(hours=5, minutes=30)  # Adjusting for IST
    # radius_km = 1  # Radius in kilometers
    # print("Time taken to set current time:", d - c, "seconds")
    df = pd.read_csv("static/df_model.csv")
    df = df.dropna(subset=["pickup_lat"])

    df = df.merge(agg_df, on="crn_order_id", how="left")

    # Missing values → 0 for sum, False for boolean
    df["got_trip_sum_true"] = df["got_trip_sum_true"].fillna(0).astype(int)
    df["got_trip_sum_false"] = df["got_trip_sum_false"].fillna(0).astype(int)
    added_penalty = False



    if last_hotspot_instance:
        added_penalty = True
        today = get_utc_time()

        time_of_last_hotspot = abs(today - last_hotspot_instance.created_at)
        if last_hotspot_instance.reached_hotspot_timestamp:
            time_of_last_hotspot = abs(today - last_hotspot_instance.reached_hotspot_timestamp )
        if last_hotspot_instance.got_trip:
            avatonn_porter_trip_instance = await get_tuple_instance(session , AvaronnPorterTrip , {"avaronn_porter_trip_uuid" : last_hotspot_instance.avaronn_porter_trip_uuid})
            time_of_last_hotspot = abs(today - avatonn_porter_trip_instance.trip_off_time)
        if time_of_last_hotspot < timedelta(minutes=20):
            remaining_time = timedelta(minutes=20) - time_of_last_hotspot
            remaining_minutes = int(remaining_time.total_seconds() // 60)
            raise ForbiddenError(f"{remaining_minutes} mins")
    
    #V0
    # cluster_dict = get_best_cluster(
    #     driver_lat=input_coords[0],
    #     driver_lon=input_coords[1],
    #     df=df,
    #     range_km=5.0,
    #     eps_km=0.5,
    #     min_samples=5
    # )
    #V1
    # cluster_dict = find_closest_hotspot(
    #     driver_lat=input_coords[0],
    #     driver_lon=input_coords[1],
    #     hotspots_df=df,
    #     min_distance_km=2.5
    # )
    
    #V2
    cluster_dict = score_nearby_pickups(
        df,
        query_lat=input_coords[0],
        query_long=input_coords[1],
        current_time= current_time,
        radius_km=5,
        current_hour= current_hour,
        current_day_of_week= current_day_of_week,
        weights=None,
        penalty_km=None if added_penalty is False else 2,
        crn_order_id_occupied=crn_order_id_occupied
    )
    
    if cluster_dict.empty:
        # raise  ForbiddenError("No nearby hotspots found.")
        return success_response(request, get_hotspot_response(), "No nearby hotspots found.", True) 
    # Uncomment the following line to see the full cluster dictionary  
    # print("cluster_dict", cluster_dict.iloc[0])
    crn_order_id = cluster_dict['crn_order_id'].iloc[0]
    hotspot_point = {
        "latitude": round(cluster_dict['pickup_lat'].iloc[0], 5),
        "longitude": round(cluster_dict['pickup_long'].iloc[0], 5)
    }
    
    route = await get_route(input_coords[0],
                        input_coords[1],
                        hotspot_point['latitude'],
                        hotspot_point['longitude']
                        )
    
    hotspot_route_uuid = await save_route_to_db(session , driver_uuid , route, crn_order_id)
    route["hotspot_route_uuid"] = hotspot_route_uuid
    await session.commit()
    await session.close()

    return success_response(request , get_hotspot_response(**route) , "get hotspot successfully" , False)
