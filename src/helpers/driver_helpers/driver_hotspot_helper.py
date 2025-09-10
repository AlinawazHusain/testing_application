import asyncio
from collections import Counter
from math import atan2, cos, radians, sin, sqrt
from statistics import mode
import googlemaps
import polyline
from db.database_operations import insert_into_table
from models.hotspot_routes_models import HotspotRoutes
from schemas.v1.driver_schemas.driver_hotspot_schema import Coordinate
from sqlalchemy.ext.asyncio import AsyncSession
from settings.credential_settings import credential_setting
from shapely.geometry import LineString, Point
from geoalchemy2.shape import from_shape
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from typing import Dict, Tuple
from collections import Counter
import geopandas as gpd
from shapely.geometry import Point
from geopy.distance import geodesic


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    km = 6371 * c  # Radius of earth in kilometers
    return km


def filter_points_in_range(
    driver_lat: float,
    driver_lon: float,
    df: pd.DataFrame,
    range_km: float = 10.0
) -> pd.DataFrame:
    """
    Filter points within the specified range of the driver's location.
    Uses vectorized operations for better performance.
    Args:
        driver_lat (float): Driver's latitude
        driver_lon (float): Driver's longitude
        df (pd.DataFrame): DataFrame containing 'latitude' and 'longitude' columns
        range_km (float): Range in kilometers to filter points
    Returns:
        pd.DataFrame: Filtered DataFrame containing only points within range
    """
    # Vectorized distance calculation using haversine formula
    distances = np.vectorize(haversine_distance)(
        driver_lat, driver_lon,
        df['pickup_lat'].values,
        df['pickup_long'].values
    )
    # Filter points within range
    mask = distances <= range_km
    filtered_df = df[mask].copy()
    filtered_df['distance'] = distances[mask]
    return filtered_df



def cluster_locations(
    df: pd.DataFrame,
    eps_km: float = 0.5,
    min_samples: int = 5
) -> Tuple[pd.DataFrame, Dict]:
    """
    Cluster locations using DBSCAN algorithm.
    Args:
        df (pd.DataFrame): DataFrame containing 'latitude' and 'longitude' columns
        eps_km (float): Maximum distance between points in a cluster (in kilometers)
        min_samples (int): Minimum number of points required to form a cluster
    Returns:
        Tuple[pd.DataFrame, Dict]: DataFrame with cluster labels and cluster statistics
    """
    # Convert coordinates to radians for DBSCAN
    coords = df[['pickup_lat', 'pickup_long']].values
    # Convert eps from kilometers to degrees (approximate)
    eps_degrees = eps_km / 111.0  # 1 degree ≈ 111 km
    # Perform DBSCAN clustering
    clustering = DBSCAN(
        eps=eps_degrees,
        min_samples=min_samples,
        metric='haversine', # Use haversine distance for geographic coordinates
        n_jobs=-1  # Use all available CPU cores
    ).fit(coords)
    # Add cluster labels to DataFrame
    df['cluster'] = clustering.labels_
    # Calculate cluster statistics using vectorized operations
    unique_clusters = np.unique(clustering.labels_)
    cluster_stats = {}
    for cluster_id in unique_clusters:
        if cluster_id != -1:  # Skip noise points
            mask = df['cluster'] == cluster_id
            cluster_points = df[mask]
            cluster_stats[cluster_id] = {
                'count': len(cluster_points),
                'center_lat': cluster_points['pickup_lat'].mode(),
                'center_lon': cluster_points['pickup_long'].mode()
            }
    return df, cluster_stats



# def get_best_cluster(
#     driver_lat: float,
#     driver_lon: float,
#     df: pd.DataFrame,
#     range_km: float = 10.0,
#     eps_km: float = 0.5,
#     min_samples: int = 5
# ) -> Dict:
#     """
#     Get the best cluster of points within range of the driver's location.
#     Args:
#         driver_lat (float): Driver's latitude
#         driver_lon (float): Driver's longitude
#         df (pd.DataFrame): DataFrame containing 'latitude' and 'longitude' columns
#         range_km (float): Range in kilometers to filter points
#         eps_km (float): Maximum distance between points in a cluster
#         min_samples (int): Minimum number of points required to form a cluster
#     Returns:
#         Dict: Information about the best cluster
#     """
#     # Filter points within range
#     filtered_df = filter_points_in_range(driver_lat, driver_lon, df, range_km)
#     if len(filtered_df) == 0:
#         # logger.warning("No points found within the specified range")
#         return None
#     # Perform clustering
#     clustered_df, cluster_stats = cluster_locations(filtered_df, eps_km, min_samples)
#     if not cluster_stats:
#         # logger.warning("No valid clusters found")
#         return None
#     # Find the cluster with the most points
#     best_cluster_id = max(cluster_stats.items(), key=lambda x: x[1]['count'])[0]
#     best_cluster = cluster_stats[best_cluster_id]
#     # Add additional information
#     best_cluster['cluster_id'] = best_cluster_id
#     # best_cluster['points'] = clustered_df[clustered_df['cluster'] == best_cluster_id].to_dict('records')
#     cluster_points = clustered_df[clustered_df['cluster'] == best_cluster_id]
#     # Calculate the mode of latitudes and longitudes
#     lat_long_pairs = list(zip(cluster_points['pickup_lat'], cluster_points['pickup_long']))
#     # Calculate the mode of the (lat, long) pairs
#     pair_counts = Counter(lat_long_pairs)
#     most_common_pair, count = pair_counts.most_common(1)[0] if pair_counts else (None, None)
#     mode_latitude = mode_longitude = None
#     if most_common_pair:
    
#         lat_long_pairs = list(zip(cluster_points['pickup_lat'], cluster_points['pickup_long']))

#     # Calculate the mode of the (lat, long) pairs
#     pair_counts = Counter(lat_long_pairs)
#     most_common_pair, count = pair_counts.most_common(1)[0] if pair_counts else (None, None)

#     if most_common_pair:
#         # If mode is found, use it
#         mode_latitude, mode_longitude = most_common_pair
#         mode_latitude, mode_longitude = most_common_pair
#     else:
#         # If mode is not found, use the nearest point to the cluster center
#         cluster_center_lat = cluster_points['pickup_lat'].mean()
#         cluster_center_long = cluster_points['pickup_long'].mean()
#         cluster_points['distance_to_center'] = (
#             (cluster_points['pickup_lat'] - cluster_center_lat) ** 2 +
#             (cluster_points['pickup_long'] - cluster_center_long) ** 2
#         )
#         nearest_point = cluster_points.loc[cluster_points['distance_to_center'].idxmin()]
#         mode_latitude = nearest_point['pickup_lat']
#         mode_longitude = nearest_point['pickup_long']
#         # # Calculate the mode of latitudes and longitudes
#     # lat_mode = mode(cluster_points['pickup_lat']).mode
#     # long_mode = mode(cluster_points['pickup_long']).mode

#     # if len(lat_mode) > 0 and len(long_mode) > 0:
#     #     # If mode is found, use it
#     #     mode_latitude = lat_mode[0]
#     #     mode_longitude = long_mode[0]
#     # else:
#     #     # If mode is not found, use the nearest point to the cluster center
#     #     cluster_center_lat = cluster_points['pickup_lat'].mean()
#     #     cluster_center_long = cluster_points['pickup_long'].mean()
#     #     cluster_points['distance_to_center'] = (
#     #         (cluster_points['pickup_lat'] - cluster_center_lat) ** 2 +
#     #         (cluster_points['pickup_long'] - cluster_center_long) ** 2
#     #     )
#     #     nearest_point = cluster_points.loc[cluster_points['distance_to_center'].idxmin()]
#     #     mode_latitude = nearest_point['pickup_lat']
#     #     mode_longitude = nearest_point['pickup_long']

#     # Assign the mean values to the best_cluster dictionary
#     best_cluster['latitude'] = float(mode_latitude)
#     best_cluster['longitude'] = float(mode_longitude)
#     # # Add performance metrics
#     best_cluster['total_points_processed'] = len(df)
#     best_cluster['points_in_range'] = len(filtered_df)
#     return best_cluster




import numpy as np
import pandas as pd

# Vectorized Haversine formula
def haversine_np(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in km
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c  # in kilometers

def find_closest_hotspot(driver_lat, driver_lon, hotspots_df, min_distance_km=2.5):
    # Compute all distances at once (vectorized)
    distances = haversine_np(driver_lat, driver_lon, hotspots_df['pickup_lat'].values, hotspots_df['pickup_long'].values)

    # Filter based on min distance
    valid_indices = np.where(distances > min_distance_km)[0]

    if len(valid_indices) == 0:
        return None

    # Get the index of the closest valid hotspot
    closest_idx = valid_indices[np.argmin(distances[valid_indices])]

    return {
        'pickup_lat': hotspots_df.iloc[closest_idx]['pickup_lat'],
        'pickup_long': hotspots_df.iloc[closest_idx]['pickup_long'],
        'distance_km': distances[closest_idx]
    }

import numpy as np
import pandas as pd

def score_nearby_pickups(
    df,
    query_lat,
    query_long,
    radius_km,
    current_hour,
    current_day_of_week,
    weights=None
):
    """
    Scores nearby pickups based on multiple weighted factors:
    - area_type (commercial, residential, unknown)
    - distance (closer = higher score)
    - pickup_matches_any_drop (boolean)
    - hour_of_day match (boolean)
    - day_of_week match (boolean)

    Parameters:
    - df: DataFrame containing the data with necessary columns.
    - query_lat, query_long: query coordinates.
    - radius_km: radius in km to filter pickups.
    - current_hour: int, hour of day [0-23] to match.
    - current_day_of_week: string (e.g., 'Wednesday') to match day of week.
    - weights: dict, weights for each factor (optional, will use defaults if None).

    Returns:
    - Sorted DataFrame of pickups within radius with added 'score' column.
    """

    # Set default weights if none provided
    if weights is None:
        weights = {
            'area_weight_commercial': 1.0,
            'area_weight_residential': 0.2,
            'area_weight_unknown': 0.5,
            'pickup_matches_any_drop_weight': 0.7,
            'hour_match_weight': 1,
            'day_match_weight': 1,
            'distance_weight': 0.5
        }

    # Copy df and drop missing values in critical columns
    df = df.copy()
    df = df.dropna(subset=[
        'pickup_lat',
        'pickup_long',
        'area_type',
        'hour_of_day',
        'day_of_week',
        'pickup_matches_any_drop'
    ])

    # Calculate distance from query point to pickup location
    def safe_distance(row):
        try:
            return geodesic((query_lat, query_long), (row['pickup_lat'], row['pickup_long'])).km
        except Exception:
            return np.nan

    df['distance_km'] = df.apply(safe_distance, axis=1)
    nearby_df = df[df['distance_km'] <= radius_km].copy()

    if nearby_df.empty:
      nearby_df = df[df['distance_km'] <= radius_km+5].copy()
      # return nearby_df  # no nearby pickups within radius
    if nearby_df.empty:
      return nearby_df  # no nearby pickups within radius +5 km

    # Map area_type to weights
    area_weights_map = {
        'commercial': weights['area_weight_commercial'],
        'residential': weights['area_weight_residential'],
        'unknown': weights['area_weight_unknown']
    }
    nearby_df['area_weight'] = nearby_df['area_type'].map(area_weights_map).fillna(weights['area_weight_unknown'])

    # Distance score: closer distance → higher score (inverse scaled)
    nearby_df['distance_score'] = 1 / (1 + nearby_df['distance_km'])  # avoid divide by zero

    # Normalize driver_rating to 0-1 scale (assuming max 5)

    # Compute boolean matches and convert to float 1/0 for weighting
    nearby_df['pickup_matches_any_drop'] = nearby_df['pickup_matches_any_drop'].astype(bool).astype(float)

    nearby_df['hour_match'] = (nearby_df['hour_of_day'] == current_hour).astype(float)

    # Normalize day_of_week strings for case-insensitive matching
    nearby_df['day_of_week_norm'] = nearby_df['day_of_week'].str.strip().str.lower()
    current_day_norm = current_day_of_week.strip().lower()
    nearby_df['day_match'] = (nearby_df['day_of_week_norm'] == current_day_norm).astype(float)

    # Combine weights as per given importance weights
    nearby_df['score'] = (
        nearby_df['area_weight'] * weights['area_weight_commercial'] +  # area_weight already weighted; correct below
        nearby_df['pickup_matches_any_drop'] * weights['pickup_matches_any_drop_weight'] +
        nearby_df['hour_match'] * weights['hour_match_weight'] +
        nearby_df['day_match'] * weights['day_match_weight'] +
        nearby_df['distance_score'] * weights['distance_weight']
    )

    # Note: The above adds area_weight weighted again by weights['area_weight_commercial']
    # This double weighting is a mistake: area_weight column already holds weighted value.
    # Correct by not multiplying area_weight by weight again, instead multiply weights inside mapping

    # Fix that by re-mapping area_weight properly (no need to multiply again):


def score_nearby_pickups(
    df,
    query_lat,
    query_long,
    radius_km,
    current_time,
    current_hour,
    current_day_of_week,
    weights=None,
    overload_km=5.0,
    penalty_km=None,
    crn_order_id_occupied=[]
):
    if weights is None:
        weights = {
            'area_weight_commercial': 1.0,
            'area_weight_residential': 0.2,
            'area_weight_unknown': 0.5,
            'pickup_matches_any_drop_weight': 0.7,
            'hour_match_weight': 1,
            'day_match_weight': 1,
            'distance_weight': 0.5
        }
    import time
    print("Starting scoring nearby pickups...")
    a = time.time()

    df_copy = df.copy()
    df_copy = df_copy[~df_copy['crn_order_id'].isin(crn_order_id_occupied)].copy()
    b = time.time()
    print(df_copy.columns)
    print(f"Copying DataFrame took {b - a:.4f} seconds")
    # print(df_copy.columns)
    df_copy = df_copy.dropna(subset=[
        'pickup_lat',
        'pickup_long',
        'area_type',
        'hour_of_day',
        'day_of_week',
        'pickup_matches_any_drop'
    ])
    c = time.time()
    print(f"Dropping NaN values took {c - b:.4f} seconds")
    # def safe_distance(row):
    #     try:
    #         return geodesic((query_lat, query_long), (row['pickup_lat'], row['pickup_long'])).km
    #     except Exception:
    #         return np.nan
    d = time.time()
    # print(f"Defining safe_distance function took {d - c:.4f} seconds")
    # df_copy['distance_km'] = df_copy.apply(safe_distance, axis=1)
    import numpy as np

    def haversine_np(lat1, lon1, lat2, lon2):
        R = 6371  # Earth's radius in kilometers

        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c

    # Vectorized for DataFrame columns:
    df_copy['distance_km'] = haversine_np(
        query_lat,
        query_long,
        df_copy['pickup_lat'].values,
        df_copy['pickup_long'].values
    )

    e = time.time()
    print(f"Calculating distances took {e - d:.4f} seconds")
    if penalty_km is None:
        nearby_df = df_copy[df_copy['distance_km'] <= radius_km].copy()
        print("******NO PENALTY KM PROVIDED, USING RADIUS KM ONLY******")
    else:
        nearby_df = df_copy[(df_copy['distance_km'] >= penalty_km) & (df_copy['distance_km'] <= radius_km)].copy()
        print(f"******PENALTY KM PROVIDED, USING PENALTY KM {penalty_km} AND RADIUS KM {radius_km}******")
    f = time.time()
    print(f"Filtering nearby pickups took {f - e:.4f} seconds")

    if nearby_df.empty:
        nearby_df = df_copy[df_copy['distance_km'] <= radius_km + overload_km].copy()
        if nearby_df.empty:
            print("No nearby pickups found within the specified radius.")
            return pd.DataFrame()  # Return empty DataFrame if no nearby pickups found
        # return nearby_df

    day_name_to_num = {
    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
    'friday': 4, 'saturday': 5, 'sunday': 6
    }
    nearby_df['day_num'] = nearby_df['day_of_week'].str.strip().str.lower().map(day_name_to_num)
    nearby_df['diff_in_week_days'] = (nearby_df['day_num'] - current_time.weekday()).abs()
    nearby_df['start_time'] = pd.to_datetime(nearby_df['start_time'], errors='coerce')
    nearby_df['diff_start_current_minutes'] = ((current_time - nearby_df['start_time']).dt.total_seconds() / 60).abs()
    print(nearby_df.columns)
    print(nearby_df.head())
    g = time.time()
    print(f"Calculating time differences took {g - f:.4f} seconds")

    

    # Map area_type to weights
    area_weights_map = {
        'commercial': weights['area_weight_commercial'],
        'residential': weights['area_weight_residential'],
        'unknown': weights['area_weight_unknown']
    }
    # Apply area weights
    nearby_df['area_weight'] = nearby_df['area_type'].map(area_weights_map).fillna(weights['area_weight_unknown'])

    nearby_df['distance_score'] = 1 / (1 + nearby_df['distance_km']/radius_km)

    # nearby_df['driver_rating_norm'] = nearby_df['driver_rating'] / 5

    nearby_df['pickup_matches_any_drop'] = nearby_df['pickup_matches_any_drop'].astype(bool).astype(float)

    nearby_df['diff_in_week_days_norm'] = 1 - (nearby_df['diff_in_week_days'] / 6.0)  # Normalize to [0, 1] range

    # nearby_df['got_trip_true'] = nearby_df['got_trip_sum_true'].astype(bool).astype(float)
    # got_trip_sum_false
    nearby_df["true_ratio"] = np.where(
    (nearby_df["got_trip_sum_true"] + nearby_df["got_trip_sum_false"]) == 0,
    0,  # default value when both zero
    nearby_df["got_trip_sum_true"] / (nearby_df["got_trip_sum_true"] + nearby_df["got_trip_sum_false"])
)

    nearby_df["false_ratio"] = np.where(
    (nearby_df["got_trip_sum_true"] + nearby_df["got_trip_sum_false"]) == 0,
    0,  # default value when both zero
    nearby_df["got_trip_sum_false"] / (nearby_df["got_trip_sum_true"] + nearby_df["got_trip_sum_false"])
)

    def normalize_minutes(series):
        # Clip values between 0 and 1440
        clipped = series.clip(lower=0, upper=1440)
        # Min-max normalization between 0 and 1440
        return clipped / 1440
    nearby_df['diff_start_current_minutes_norm'] = 1- normalize_minutes(nearby_df['diff_start_current_minutes'])

    h = time.time()
    print(f"Calculating scores took {h - g:.4f} seconds")
    # nearby_df['hour_match'] = (nearby_df['hour_of_day'] == current_hour).astype(float)

    # nearby_df['day_of_week_norm'] = nearby_df['day_of_week'].str.strip().str.lower()
    # current_day_norm = current_day_of_week.strip().lower()
    # nearby_df['day_match'] = (nearby_df['day_of_week_norm'] == current_day_norm).astype(float)

    nearby_df['score'] = (
        nearby_df['area_weight'] * 1.0 +
        nearby_df['pickup_matches_any_drop'] * weights['pickup_matches_any_drop_weight'] +
        nearby_df['diff_start_current_minutes_norm'] * weights['hour_match_weight'] +
        nearby_df['diff_in_week_days_norm'] * weights['day_match_weight'] +
        nearby_df['distance_score'] * weights['distance_weight'] +
        nearby_df['true_ratio'] * 1.2 -  # Adjust weight as needed
        nearby_df['false_ratio'] * 0.6  # Adjust weight as needed
    )

    sorted_nearby_df = nearby_df.sort_values(by='score', ascending=False)
    i = time.time()
    print(f"Sorting DataFrame took {i - h:.4f} seconds")
    # # Drop helper column
    # sorted_nearby_df.drop(columns=['day_of_week_norm'], inplace=True)

    return sorted_nearby_df


# def find_closest_hotspot(driver_lat, driver_lon, hotspots_df, min_distance_km=2.5):
#     closest_hotspot = None
#     closest_distance = float('inf')

#     # Iterate through each hotspot
#     for _, row in hotspots_df.iterrows():
#         hotspot_location = (row['pickup_lat'], row['pickup_long'])
#         current_location = (driver_lat, driver_lon)

#         # Calculate the distance between the current location and the hotspot
#         distance = geodesic(current_location, hotspot_location).km

#         # Check if the distance is greater than the minimum distance and is the closest so far
#         if distance > min_distance_km and distance < closest_distance:
#             closest_hotspot = {
#                 'pickup_lat': row['pickup_lat'],
#                 'pickup_long': row['pickup_long'],
#                 'distance_km': distance
#             }
#             closest_distance = distance

#     return closest_hotspot



async def get_route(origin_lat, origin_lng, dest_lat, dest_lng, mode='driving'):
    """
    Get route directions between two lat/lng points using Google Maps Directions API.

    Args:
        api_key (str): Your Google Maps API key.
        origin_lat (float): Latitude of the origin.
        origin_lng (float): Longitude of the origin.
        dest_lat (float): Latitude of the destination.
        dest_lng (float): Longitude of the destination.
        mode (str): Mode of transport ('driving', 'walking', 'bicycling', 'transit')

    Returns:
        dict: Directions API response, including route steps and polyline.
    """
    api_key = credential_setting.google_map_api_key
    gmaps = googlemaps.Client(key=api_key)
    origin = f"{origin_lat},{origin_lng}"
    destination = f"{dest_lat},{dest_lng}"

    directions_result = await asyncio.to_thread(
        gmaps.directions,
        origin,
        destination,
        mode=mode
    )
    if not directions_result:
        raise Exception("No route found")

    route = directions_result[0]
    leg = route['legs'][0]



    overview_poly = route['overview_polyline']['points']
    coordinates = polyline.decode(overview_poly) 

    COORDINATES = [{"lat": lat, "lng": lng} for lat, lng in coordinates]


    navigation = []
    for step in leg['steps']:
        step_poly = step['polyline']['points']
        step_coords = polyline.decode(step_poly)
        navigation.append({
            "start_location": Coordinate(**step['start_location']),
            "end_location": Coordinate(**step['end_location']),
            "distance_meters": step['distance']['value'],
            "duration_seconds": step['duration']['value'],
            "instruction": step.get('html_instructions', ''),
            "polyline": step_poly,
            "navigation": [Coordinate(lat = lat, lng = lng) for lat, lng in step_coords]
        })
    
    route =  {
        "start": Coordinate(**leg['start_location']),
        "end": Coordinate(**leg['end_location']),
        "distance_meters": leg['distance']['value'],
        "distance_text": leg['distance']['text'],
        "duration_seconds": leg['duration']['value'],
        "duration_text": leg['duration']['text'],
        "overview_polyline": overview_poly,
        "overview_navigation": [Coordinate(lat = c["lat"], lng = c["lng"]) for c in COORDINATES],
        "navigation": navigation
    }

    return route



async def save_route_to_db(session:AsyncSession , driver_uuid:str , route, crn_order_id):
    start = route['start']
    end = route['end']
    poly = route['overview_polyline']
    coords = polyline.decode(poly) 
    linestring = "LINESTRING({})".format(
        ", ".join(f"{lng} {lat}" for lat, lng in coords)
    )
    
    linestring_geom = from_shape(LineString([(lng, lat) for lat, lng in coords]), srid=4326)
    start_point_geom = from_shape(Point(start.lng, start.lat), srid=4326)
    end_point_geom = from_shape(Point(end.lng, end.lat), srid=4326)
    
    route_data = {
        "driver_uuid": driver_uuid,
        "start_lat": start.lat,
        "start_lng": start.lng,
        "start_location" : start_point_geom,
        "end_lat": end.lat,
        "end_lng": end.lng,
        "end_location" : end_point_geom,
        "route_distance_meters" : route['distance_meters'],
        "route_distance_text" :  route['distance_text'],
        "route_duration_seconds" : route['duration_seconds'],
        "route_duration_text" : route['duration_text'],
        "route_to_hotspot" : linestring_geom,
        "route_overview_polyline" : poly,
        "route_geom" : linestring,
        "crn_order_id": crn_order_id
    }
    # from sqlalchemy import text

    # query = text("""
    # INSERT INTO public.hotspot_routes (
    #     driver_uuid,
    #     start_lat,
    #     start_lng,
    #     start_location,
    #     end_lat,
    #     end_lng,
    #     end_location,
    #     route_distance_meters,
    #     route_distance_text,
    #     route_duration_seconds,
    #     route_duration_text,
    #     route_to_hotspot,
    #     route_overview_polyline,
    #     route_geom
    # )
    # VALUES (
    #     :driver_uuid,
    #     :start_lat,
    #     :start_lng,
    #     :start_location,    -- if using PostGIS geometry as WKT string
    #     :end_lat,
    #     :end_lng,
    #     :end_location,
    #     :route_distance_meters,
    #     :route_distance_text,
    #     :route_duration_seconds,
    #     :route_duration_text,
    #     :route_to_hotspot,
    #     :route_overview_polyline,
    #     :route_geom
    # )
    # """)

    # params = {
    #     "driver_uuid": driver_uuid,
    #     "start_lat": start.lat,
    #     "start_lng": start.lng,
    #     "start_location": str(start_point_geom),     # as WKT, e.g. 'POINT(lon lat)'
    #     "end_lat": end.lat,
    #     "end_lng": end.lng,
    #     "end_location": str(end_point_geom),
    #     "route_distance_meters": route['distance_meters'],
    #     "route_distance_text": route['distance_text'],
    #     "route_duration_seconds": route['duration_seconds'],
    #     "route_duration_text": route['duration_text'],
    #     "route_to_hotspot": str(linestring_geom),
    #     "route_overview_polyline": poly,
    #     "route_geom": str(linestring)
    # }

    # route_instance = await session.execute(query, params)
    # await session.commit()

    # await session.execute(query, route_data)
    # await session.commit()
    route_instance = await insert_into_table(session , HotspotRoutes , route_data)
    return route_instance.hotspot_route_uuid