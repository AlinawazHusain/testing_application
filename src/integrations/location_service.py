import asyncio
import httpx
import random
from settings.credential_settings import credential_setting

MAX_RETRIES = 5 
CONCURRENT_LIMIT = 15
semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)


async def fetch_with_retries(url, params, timeout=15):
    """
    Perform a GET request with automatic retries for rate-limited APIs (HTTP 429).

    Implements exponential backoff with jitter for retrying requests that hit
    the rate limit, with a limit on maximum concurrent requests via a semaphore.

    Args:
        url (str): The API endpoint URL.
        params (dict): Query parameters to be sent with the request.
        timeout (int, optional): Request timeout in seconds. Defaults to 15.

    Returns:
        dict or None: JSON response data if successful, otherwise None after retries.
    """
    
    retries = 0
    backoff = 1  
    while retries < MAX_RETRIES:
        try:
            async with semaphore, httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)
                if response.status_code == 429:  # Rate limit hit
                    wait_time = backoff + random.uniform(0, 1)
                    print(f"⏳ Rate limit exceeded. Retrying in {wait_time:.2f}s...")
                    await asyncio.sleep(wait_time)
                    backoff *= 2  # Exponential backoff
                    retries += 1
                    continue  # Retry request

                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
            break
        except httpx.ConnectTimeout:
            print("⏳ Connection Timeout. Retrying...")
        except httpx.RequestError as e:
            print(f"❌ Request Error: {e}")
        except Exception as e:
            print(f"⚠️ Unexpected error: {e}")

        await asyncio.sleep(backoff)  # Wait before retrying
        backoff *= 2
        retries += 1

    return None  # Return None if all retries fail


async def get_lat_lng(address):
    """
    Retrieve latitude and longitude coordinates for a given address using 
    the Google Maps Geocoding API.

    Args:
        address (str): Full address to geocode.

    Returns:
        list[float, float]: A list containing [latitude, longitude] if successful,
        otherwise [None, None].

    Logs:
        - Error messages if API request fails or returns an unexpected response.
    """
    
    
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": credential_setting.google_map_api_key}

    data = await fetch_with_retries(base_url, params)

    if data and data.get("status") == "OK":
        location = data["results"][0]["geometry"]["location"]
        return [location["lat"], location["lng"]]

    print(f"❌ Geocoding API Error for '{address}': {data.get('error_message', 'Unknown error')}")
    return [None, None]


async def get_distance(origin, destination, start_time="now", mode="driving"):
    """
    Calculate the distance and estimated duration between two locations using 
    the Google Distance Matrix API.

    Args:
        origin (str): Starting location (address or "lat,lng").
        destination (str): Destination location (address or "lat,lng").
        start_time (str, optional): Departure time. Use "now" or UNIX timestamp. Defaults to "now".
        mode (str, optional): Mode of transport. Options include "driving", "walking", "bicycling", etc. Defaults to "driving".

    Returns:
        list[float, float]: A list containing [distance in km, duration in minutes] 
        if successful, otherwise [None, None].

    Logs:
        - API errors and response parsing issues.
    """
    
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "units": "metric",
        "key": credential_setting.google_map_api_key,
        "departure_time": start_time,
        "traffic_model": "optimistic"
    }

    data = await fetch_with_retries(base_url, params, timeout=30)

    if data and data.get("status") == "OK":
        try:
            distance_value = data["rows"][0]["elements"][0]["distance"]["value"]
            duration_value = data["rows"][0]["elements"][0]["duration"]["value"]
            duration_minutes = round(duration_value / 60, 2)
            return [distance_value / 1000, duration_minutes]
        except (KeyError, IndexError):
            print("⚠️ Error: Unexpected response format in Distance API")

    print(f"❌ Distance API Error: {data.get('error_message', 'Unknown error')}")
    return [None, None]




async def get_location_from_lat_lng(lat, lng):
    api_key = credential_setting.google_map_api_key
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={api_key}"
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
        
            if response.status_code != 200:
                return f"Error: HTTP {response.status_code}"

            data = response.json()
            if data.get("status") != "OK":
                return f"Error: {data.get('status')}"

            address = data["results"][0]["formatted_address"]
            return address
    except:
        return "Unable to fetch location"





async def get_location_name(lat: float, lon: float) -> str | None:
    """
    Reverse geocode a latitude and longitude to a human-readable address 
    using the OpenStreetMap Nominatim API.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.

    Returns:
        str | None: Display name (address string) if found, otherwise None.

    Notes:
        - The request includes a custom User-Agent as required by Nominatim's usage policy.
    """
    try:
        # url = "https://nominatim.openstreetmap.org/reverse"
        # params = {
        #     "format": "json",
        #     "lat": lat,
        #     "lon": lon,
        #     "zoom": 18,
        #     "addressdetails": 1
        # }

        headers = {
            "User-Agent": "AvaronnLocationService/1.0"
        }
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"

        async with httpx.AsyncClient(timeout=10) as client:
            # response = await client.get(url, params=params, headers=headers)
            response = await client.get(url,  headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data.get("display_name")
        else:
            location = await get_location_from_lat_lng(lat , lon)
            return location
    except:
        location = await get_location_from_lat_lng(lat , lon)
        return location
        
    

def generate_google_maps_link(lat, lng, zoom=15):
    return f"https://www.google.com/maps?q={lat},{lng}&z={zoom}"

def generate_google_maps_path_link(start_lat , start_lng , end_lat , end_lng):
    return f"https://www.google.com/maps/dir/{start_lat},{start_lng}/{end_lat},{end_lng}"




async def get_location_details_from_pincode(pincode: str):
    
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={pincode}&key={credential_setting.google_map_api_key}"
    
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        data = response.json()

        if not data.get("results"):
            return None

        components = data["results"][0]["address_components"]

        city = state = country = area = None

        for component in components:
            types = component["types"]

            if "locality" in types:
                city = component["long_name"]
            elif "administrative_area_level_2" in types and not city:
                city = component["long_name"] 
            elif "administrative_area_level_1" in types:
                state = component["long_name"]
            elif "country" in types:
                country = component["long_name"]
            elif "sublocality" in types or "sublocality_level_1" in types or "neighborhood" in types:
                area = component["long_name"]

        return {
            "area": area,
            "city": city,
            "state": state,
            "country": country
        }

