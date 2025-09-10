import asyncio
from math import atan2, cos, radians, sin, sqrt
import httpx
from sqlalchemy import inspect
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

async def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))



async def get_structured_can_data(data):
    structured_data = {}
    for k, v in data.items():
        for j, l in v.items():
            structured_data[f"{k}_{j}"] = l
    return structured_data







async def produce_can_data(token , vehicleno):
    api_params = {
        "token" : token,
        "vehicleno" : vehicleno
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post("https://apiplatform.intellicar.in/api/standard/getlatestcan", json=api_params, timeout=5)
        if response.status_code == 200 :
            response_data = response.json()
            try:
                data = await get_structured_can_data(response_data["data"])
                data["vehicle_number"] = vehicleno
                return data
            except:
                print(f"unable to push can data for {vehicleno}")
        
        elif response.status_code == 401:
            return False



async def produce_location_data(token , vehicleno):
    api_params = {
        "token" : token,
        "vehicleno" : vehicleno
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post("https://apiplatform.intellicar.in/api/standard/getlastgpsstatus", json = api_params , timeout=10)
        if response.status_code == 200 :
            response_data = response.json()
            try:
                data = response_data["data"]
                data["vehicle_number"] = vehicleno
                data["location"]=from_shape(Point(data["lng"], data["lat"]))
                return data
            except:
                print(f"unable to push location data for {vehicleno}")
        
        elif response.status_code == 401:
            return False
   
    
async def get_token(username , password):
    token_data = {"username": username, "password": password}
    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post("https://apiplatform.intellicar.in/api/standard/gettoken", json = token_data , timeout=10)
        if token_response.status_code == 200:
            token_data = token_response.json()
            token = token_data["data"]["token"]
            return token
        else:
            return "Unable to get token"
    

async def start_telematics_data( username , password):
    
    token = await get_token(username , password)
    vehicle_status_dict = static_table_settings.static_table_data["VEHICLE_STATUS"]
    
    idle_status_uuid =  next((k for k, v in vehicle_status_dict.items() if v == 'Idle'), None)
    running_status_uuid =  next((k for k, v in vehicle_status_dict.items() if v == 'Running'), None)
    inactive_status_uuid = next((k for k , v in vehicle_status_dict.items() if v == "Inactive") , None)
    
    
    api_params = {"token" : token , "username" : username}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post("https://apiplatform.intellicar.in/api/standard/listvehicles", json=api_params, timeout=10)
        if response.status_code == 200 :
            response_data = response.json()
            try:
                data = response_data["data"]
                vehicle_list = [i["vehicleno"] for i in data]
                while True:
                    for veh in vehicle_list:
                        try:
                            can_data = await produce_can_data(token , veh)
                            if not can_data:
                                token = await get_token(username , password)
                            
                            await asyncio.sleep(1)
                            location_data = await produce_location_data(token , veh)
                            if not location_data:
                                token = await get_token(username , password)
                            
                            if can_data:
                                async for session in get_async_db():
                                    model_columns = {c.key for c in inspect(CANData).mapper.column_attrs}

                                    filtered_data = {k: v for k, v in can_data.items() if k in model_columns}
                                    session.add(CANData(**filtered_data))
                                    vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_number" : veh , "is_enable" : True})
                                    if vehicle_instance and vehicle_instance.vehicle_status != inactive_status_uuid:
                                        if can_data["vehicle_speed_value"] == 0:
                                            vehicle_instance.vehicle_status = idle_status_uuid
                                        else:
                                            vehicle_instance.vehicle_status = running_status_uuid
                                        # if can_data["soc_value"] <25:
                                        #     mfo_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : vehicle_instance.mfo_uuid , "is_enable" : True})
                                        #     if mfo_instance:
                                        #         title = "SOC Alert !"
                                        #         message = f"Your Vehicle {veh} have LOW SOC - SOC value {can_data["soc_value"]}."
                                        #         send_fcm_notification(mfo_instance.fcm_token ,title , message)
                                                    
                                            
                                    await session.commit()
                                    await session.close()

                                
                            if location_data:
                                async for session in get_async_db():
                                    vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_number" : veh , "is_enable" : True})
                                    if vehicle_instance:
                                        vehicle_hub_mapping = await get_tuple_instance(session , VehicleHubMapping , {"vehicle_uuid" : vehicle_instance.vehicle_uuid , "is_enable" : True})
                                        if vehicle_hub_mapping:
                                            vehicle_hub_instance = await get_tuple_instance(session , HubAddressBook , {"hub_address_book_uuid" : vehicle_hub_mapping.hub_address_book_uuid})
                                            vehicle_to_hub_distance = await haversine(location_data["lat"] , location_data["lng"],vehicle_hub_instance.hub_lat , vehicle_hub_instance.hub_lng)
                                            if vehicle_to_hub_distance > 80 and vehicle_instance.vehicle_at_hub:
                                                vehicle_instance.vehicle_at_hub = False
                                                mfo_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : vehicle_instance.mfo_uuid , "is_enable" : True})
                                                if mfo_instance:
                                                    title = "Vehicle Update"
                                                    message = f"Your Vehicle {veh} has just left the hub premises."
                                                    send_fcm_notification(mfo_instance.fcm_token ,title , message)
                                                    
                                            elif vehicle_to_hub_distance <=80 and not vehicle_instance.vehicle_at_hub:
                                                vehicle_instance.vehicle_at_hub = True
                                                mfo_instance = await get_tuple_instance(session , MfoMain , {"mfo_uuid" : vehicle_instance.mfo_uuid , "is_enable" : True})
                                                if mfo_instance:
                                                    title = "Vehicle Update"
                                                    message = f"Your Vehicle {veh} is come back to hub premises."
                                                    send_fcm_notification(mfo_instance.fcm_token ,title , message)
                                                    
                                    model_columns = {c.key for c in inspect(VehicleLocation).mapper.column_attrs}

                                    filtered_data = {k: v for k, v in location_data.items() if k in model_columns}

                                    session.add(VehicleLocation(**filtered_data))
                                    await session.commit()
                                    await session.close()
                        except Exception as e:
                            fcms =  {
                            "UP1A.231005.007": "eVgVNrXbTtCKYc4iiuvTGm:APA91bE7Mk7hcUJPF7DDvAP-Ax-REzn0eSMaoKw0HgdTZs2xbTPdrBABQiJTJHonjZg0pj0s2RSCur1n3Uuf9Y1YlQPQRppnMNUZVKHWE07X0a41OVNZJGU",
                            "AP3A.240905.015.A2": "fmFGZmgDSlCtLhgtoX29eV:APA91bGj4PJieBfh2yrPQDdMMInPz7tOReTHIySd-Xh_UW2-n1ST3WehM4MLccWhShYbpPQNCza90TQQZKnnuX2PQLPQ5UnbYoc0bmSDbHakjyuFFS3L9qQ",
                            "UOAS34.216-174-1-1": "fTkTvlnZS_efdHd7C-sh4U:APA91bE2xzDoUUXqS4FnLGTo9CqTyRDmlSK0YCb9TeWQ_YNl4b7ExUuBjQTqTSilE_jO-NGkaBWmz7rdBq1QqjmW6X1xd9hG3Y0w7A4KvkPpe-Ietlf6YoA"
                            }
                            title = "TELEMATICS ALERT"
                            message = f"Telematics data loggind bot got some error for current loop"
                            send_fcm_notification(fcms ,title , message)
                            print(f"Error occured in telematics data for vehicle - {veh} , str{e}")
                    await asyncio.sleep(60)
            except:
                print(f"An unwanted error occured in telemeatics data")
        
        else:
            print("Error in initializing data logging....")