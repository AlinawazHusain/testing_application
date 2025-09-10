import asyncio
import httpx
from Bots.nudges_bot import haversine
from config.firebase_config import send_fcm_notification
from db.database_operations import get_tuple_instance
from db.db import get_async_db
from models.can_data_model import CANData
from models.mfo_models import MfoMain
from models.vehicle_hub_models import HubAddressBook, VehicleHubMapping
from models.vehicle_models import VehicleLocation, VehicleMain
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from settings.static_data_settings import static_table_settings

API_KEY = 'YzlkMjk3Nzc4OTQ1ZTQ4NWFkYjE2Yjk2NjAyMGI3MDdjNjM0OTQ3NTdlYjI1MjY0NDZjMDFiZmM1MDQ3NjBjNA'

BASE_URL = 'https://financer.eulerlogistics.com/api/v2/vehicle-data'
headers = {
    'X-Api-Key': API_KEY,
    'Content-Type': 'application/json'
}



async def update_vehicle(session , vehicle_number , speed , lat ,  lng):
    vehicle_status_dict = static_table_settings.static_table_data["VEHICLE_STATUS"]
    
    idle_status_uuid =  next((k for k, v in vehicle_status_dict.items() if v == 'Idle'), None)
    running_status_uuid =  next((k for k, v in vehicle_status_dict.items() if v == 'Running'), None)
    inactive_status_uuid = next((k for k , v in vehicle_status_dict.items() if v == "Inactive") , None)


    vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_number" : vehicle_number , "is_enable" : True})
    if vehicle_instance and vehicle_instance.vehicle_status != inactive_status_uuid:
        if speed == 0:
            vehicle_instance.vehicle_status = idle_status_uuid
        else:
            vehicle_instance.vehicle_status = running_status_uuid

    if vehicle_instance:
        vehicle_hub_mapping = await get_tuple_instance(session , VehicleHubMapping , {"vehicle_uuid" : vehicle_instance.vehicle_uuid , "is_enable" : True})
        if vehicle_hub_mapping:
            vehicle_hub_instance = await get_tuple_instance(session , HubAddressBook , {"hub_address_book_uuid" : vehicle_hub_mapping.hub_address_book_uuid})
            vehicle_to_hub_distance = await haversine(lat , lng ,vehicle_hub_instance.hub_lat , vehicle_hub_instance.hub_lng)
            if vehicle_to_hub_distance > 80 and vehicle_instance.vehicle_at_hub:
                vehicle_instance.vehicle_at_hub = False
                mfo_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : vehicle_instance.mfo_uuid , "is_enable" : True})
                if mfo_instance:
                    title = "Vehicle Update"
                    message = f"Your Vehicle {vehicle_number} has just left the hub premises."
                    send_fcm_notification(mfo_instance.fcm_token ,title , message)
                    
            elif vehicle_to_hub_distance <=80 and not vehicle_instance.vehicle_at_hub:
                vehicle_instance.vehicle_at_hub = True
                mfo_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : vehicle_instance.mfo_uuid , "is_enable" : True})
                if mfo_instance:
                    title = "Vehicle Update"
                    message = f"Your Vehicle {vehicle_number} is come back to hub premises."
                    send_fcm_notification(mfo_instance.fcm_token ,title , message) 
    await session.flush()
    
async def eular_data_logger():
    try:
        while(True):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(BASE_URL, headers=headers)
                    if response.status_code == 200:
                        vehicles_data = response.json()
                        async for session in get_async_db():
                            for veh in vehicles_data:
                                location = veh.get("location").split(",")
                                lat = float(location[0])
                                lng = float(location[1])
                                soc = veh.get("battery_soc")
                                odometer = veh.get("odometer")
                                speed = veh.get("speed")
                                ignition = veh.get("vehicle_mode")
                                veh_battery = veh.get("battery_voltage")
                                location = from_shape(Point(lng, lat))
                                location_data = {
                                    "vehicle_number" : veh["registration_number"],
                                    "lat" : lat,
                                    "lng" : lng,
                                    "vehbattery" : veh_battery,
                                    "ignstatus" : "ON" if ignition in [2 , 3 , '2' , '3']else "OFF",
                                    "speed" : speed,
                                    "odometer" : odometer,
                                    "location" : location
                                }
                                
                                can_data = {
                                    "vehicle_number" : veh["registration_number"],
                                    "soc_value" : soc,
                                    "odometer_value" : odometer,
                                    "vehicle_speed_value" : speed,
                                    "controller_temperature_value" : veh.get("controller_temperature" , 0.0),
                                    "motor_temperature_value" : veh.get("motor_temperature", 0.0),
                                    "current_value" : veh.get("battery_current" , 0.0),
                                    "battery_voltage_value" : veh.get("battery_voltage" , 0.0)
                                }
                                session.add(VehicleLocation(**location_data))
                                session.add(CANData(**can_data))
                                await session.flush()
                                
                                await update_vehicle(session , veh["registration_number"] , speed , lat , lng)
                            await session.commit()
                            await session.close()
            except :
                print("ERROR OCCURED IN EULAR DATA LOGGER")
            await asyncio.sleep(60)
    except Exception as e:
        print(f"Request failed: {e}")
