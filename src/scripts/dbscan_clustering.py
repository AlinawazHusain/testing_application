import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
import time
from sklearn.cluster import DBSCAN

# 1. Load your data
df = pd.read_csv("D:/avaronn-backend/src/scripts/orders_merged_new.csv")

# 2. Initialize geolocator
geolocator = Nominatim(user_agent="your-app")

# 3. Cache to avoid re-geocoding same address
address_cache = {}


counter = 1
def geocode_nominatim(address):
    global counter 
    if pd.isna(address):
        return None, None
    if address in address_cache:
        return address_cache[address]
    
    try:
        location = geolocator.geocode(address)
        if location:
            lat_lng = (location.latitude, location.longitude)
        else:
            lat_lng = (None, None)
    except:
        lat_lng = (None, None)

    address_cache[address] = lat_lng
    counter = counter+1
    if counter%100 == 0:
        print(f"records done -> {counter}" )
    time.sleep(1)  # Respect Nominatim's 1 req/sec rate limit
    print(lat_lng)
    return lat_lng

# 4. Apply to pickup addresses
print("Geocoding pickup addresses (this may take time)...")
for i in range(len(df)):
    # df.iloc[i]["lat" , "lng"]
    lat_lng = geocode_nominatim(df.iloc[i]["pickup_address"])
# df[["lat", "long"]] = df["pickup_address"].apply(
#     lambda x: pd.Series(geocode_nominatim(x))
# )

# 5. Save intermediate result to avoid repeating
df.to_csv("geocoded_orders.csv", index=False)

# 6. Drop missing lat/long
df = df.dropna(subset=["lat", "long"])

# 7. Prepare coordinates for clustering
coords = df[["lat", "long"]].to_numpy()
radians_coords = np.radians(coords)

# 8. DBSCAN Clustering
kms_per_radian = 6371.0088
epsilon = 1 / kms_per_radian  # 1 km radius
db = DBSCAN(eps=epsilon, min_samples=3, algorithm='ball_tree', metric='haversine')
df["cluster"] = db.fit_predict(radians_coords)

# 9. Add WKT Geometry column for PostGIS
df["geometry"] = df.apply(lambda row: f"POINT({row['long']} {row['lat']})", axis=1)

# 10. Save final output
df.to_csv("pickup_hotspots_postgis.csv", index=False)
print("✅ Final CSV saved as 'pickup_hotspots_postgis.csv'")
