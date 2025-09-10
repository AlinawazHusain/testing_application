import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import geodesic
from typing import Tuple, List, Dict
import logging
from math import radians, sin, cos, sqrt, atan2
import time

logger = logging.getLogger(__name__)

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
        df['latitude'].values,
        df['longitude'].values
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
    coords = df[['latitude', 'longitude']].values
    
    # Convert eps from kilometers to degrees (approximate)
    eps_degrees = eps_km / 111.0  # 1 degree ≈ 111 km
    
    # Perform DBSCAN clustering
    clustering = DBSCAN(
        eps=eps_degrees,
        min_samples=min_samples,
        metric='euclidean',
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
                'center_lat': cluster_points['latitude'].mean(),
                'center_lon': cluster_points['longitude'].mean()
            }
    
    return df, cluster_stats

def get_best_cluster(
    driver_lat: float,
    driver_lon: float,
    df: pd.DataFrame,
    range_km: float = 10.0,
    eps_km: float = 0.5,
    min_samples: int = 5
) -> Dict:
    """
    Get the best cluster of points within range of the driver's location.
    
    Args:
        driver_lat (float): Driver's latitude
        driver_lon (float): Driver's longitude
        df (pd.DataFrame): DataFrame containing 'latitude' and 'longitude' columns
        range_km (float): Range in kilometers to filter points
        eps_km (float): Maximum distance between points in a cluster
        min_samples (int): Minimum number of points required to form a cluster
        
    Returns:
        Dict: Information about the best cluster
    """
    start_time = time.time()
    
    # Filter points within range
    filtered_df = filter_points_in_range(driver_lat, driver_lon, df, range_km)
    
    if len(filtered_df) == 0:
        logger.warning("No points found within the specified range")
        return None
    
    # Perform clustering
    clustered_df, cluster_stats = cluster_locations(filtered_df, eps_km, min_samples)
    
    if not cluster_stats:
        logger.warning("No valid clusters found")
        return None
    
    # Find the cluster with the most points
    best_cluster_id = max(cluster_stats.items(), key=lambda x: x[1]['count'])[0]
    best_cluster = cluster_stats[best_cluster_id]
    
    # Add additional information
    best_cluster['cluster_id'] = best_cluster_id
    best_cluster['points'] = clustered_df[clustered_df['cluster'] == best_cluster_id].to_dict('records')
    
    # Add performance metrics
    best_cluster['processing_time'] = time.time() - start_time
    best_cluster['total_points_processed'] = len(df)
    best_cluster['points_in_range'] = len(filtered_df)
    
    return best_cluster 