import asyncio
from config.firebase_config import send_fcm_notification
from db.database_operations import fetch_from_table
from db.db import get_async_db
from models.vehicle_models import VehicleMain
from datetime import datetime, time, timedelta
from math import atan2, cos, radians, sin, sqrt
from sqlalchemy import desc, func
from db.database_operations import get_tuple_instance
from models.assignment_mapping_models import MfoVehicleMapping
from models.attendace_models import DriverAttendance
from models.can_data_model import CANData
from models.driver_models import DriverLocation, DriverMain
from models.hotspot_routes_models import HotspotRoutes
from models.porter_models import AvaronnPorterTrip
from models.vehicle_models import VehicleLocation, VehicleMain
from utils.time_utils import convert_utc_to_ist, get_utc_time
from settings.static_data_settings import static_table_settings
import json

async def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))



attendance_reminder_banner = "https://avaronnuserdatabase.s3.ap-south-1.amazonaws.com/assets/attendance_reminder.png"
attendance_reminder_banner_hindi = "https://avaronnuserdatabase.s3.ap-south-1.amazonaws.com/assets/attendance_reminder_hindi.png"
vehicle_connect_reminder_banner = "https://avaronnuserdatabase.s3.ap-south-1.amazonaws.com/assets/vehicle_connect_reminder.png"
vehicle_connect_reminder_banner_hindi = "https://avaronnuserdatabase.s3.ap-south-1.amazonaws.com/assets/vehicle_connect_reminder_hindi.png"
hotspot_reminder_banner = "https://avaronnuserdatabase.s3.ap-south-1.amazonaws.com/assets/hotspot_reminder.png"
hotspot_reminder_banner_hindi = "https://avaronnuserdatabase.s3.ap-south-1.amazonaws.com/assets/hotspot_reminder_hindi.png"

async def get_driver_nudge(session , driver_uuid):
    driver_main_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : driver_uuid})
    token = driver_main_instance.fcm_token
    nudge_data = {
        "token" : token,
        "title" : "",
        "message" : "",
        "data" : {}
    }
    today_utc = get_utc_time()
    today = convert_utc_to_ist(today_utc)
    date_only = today.date()
    before_1_min = today_utc - timedelta(minutes=1)
    before_15_min = today_utc - timedelta(minutes=15)
    today_825 = datetime.combine(date_only, time(hour=8, minute=25))
    today_835 = datetime.combine(date_only, time(hour=8, minute=35))
    today_900 = datetime.combine(date_only, time(hour=9, minute=30)) 
    today_1900 = datetime.combine(date_only, time(hour=19, minute=00)) 
    today_0007 = datetime.combine(date_only, time(hour=7, minute=00)) 
    
    if today >= today_1900 or today < today_0007:
        # print("here")
        return None
    attendance = await get_tuple_instance(
            session,
            DriverAttendance,
            {'driver_uuid': driver_uuid},
            extra_conditions=[
                func.DATE(DriverAttendance.attendance_trigger_time) == func.DATE(get_utc_time())
            ],
            order_by=[desc(DriverAttendance.id)],
            limit=1  
        )
    
    if attendance:
        attendance_states = static_table_settings.static_table_data["ATTENDANCE_STATES"]
        attendance_status = attendance_states.get(attendance.attendance_state_uuid)
        if attendance_status == "No action":
            if today<=today_835 and today>= today_825:
                nudge_data["title"] = "हाज़िरी नोटिफिकेशन"
                nudge_data["message"] = "आपने अभी तक अपनी हाज़िरी नहीं लगाई है, अभी लगाएं।"
                nudge_data["data"] = {
                    "screen_type" : "full",
                    "action_type" : "attendance_reminder",
                    "overlay_title" : "Attendance Reminder",
                    "overlay_text" : "You have not marked attendance . Mark your attendance"
                }
                nudge_data["image"] =  attendance_reminder_banner_hindi
                return nudge_data
            
        elif attendance_status == "Present":
            vehicle_reached = attendance.bluetooth_connection_time != None
            
            if not vehicle_reached and today >= today_900:
                nudge_data["title"] = "गाड़ी कनेक्ट करें"
                nudge_data["message"] = "आपने हाज़िरी लगा ली है, अब गाड़ी तक पहुँचें।"
                nudge_data["data"] = {
                    "screen_type" : "full",
                    "action_type" : "Connect Vehicle Reminder",
                    "overlay_title" : "Connect Vehicle",
                    "overlay_text" : "You have not reached vehicle . Reach vehicle now."
                }
                nudge_data["image"] = vehicle_connect_reminder_banner_hindi
                return nudge_data
    return None
            # else:
            #     porter_trip_instance = await get_tuple_instance(session ,
            #                                                 AvaronnPorterTrip ,
            #                                                 {"driver_uuid" : driver_uuid} ,
            #                                                     extra_conditions=[
            #                                                 func.DATE(AvaronnPorterTrip.trip_on_time) == func.DATE(get_utc_time())
            #                                                 ],
            #                                                 order_by=[desc(AvaronnPorterTrip.id)] ,
            #                                                 limit = 1)
                    
            #     hotspot_instance = await get_tuple_instance(session , HotspotRoutes ,{"driver_uuid" : driver_uuid} ,
            #                                                 extra_conditions=[
            #                                                 func.DATE(HotspotRoutes.created_at) == func.DATE(get_utc_time())
            #                                                 ],
            #                                                 order_by=[desc(HotspotRoutes.id)] , limit = 1)
            #     driver_location = await get_tuple_instance(session ,
            #                                                    DriverLocation ,
            #                                                    {"driver_uuid" : driver_uuid},
            #                                                    order_by = [desc(DriverLocation.id)],
            #                                                    limit = 1
            #                                                    )
                
            #     if driver_location.created_at <= before_1_min:
            #         nudge_data["title"] = "Fleetwise ऐप बंद हो गया है"
            #         nudge_data["message"] = "कृपया Fleetwise Sarthi ऐप फिर से खोलें, आपने इसे बंद कर दिया है।"
            #         nudge_data["data"] = {
            #             "screen_type" : "full",
            #             "action_type" : "App Dead",
            #             "overlay_title" : "Fleetwise saarthi Closed",
            #             "overlay_text" : "You disconnected from fleetwise saarthi open the app again"
            #         }
            #         return nudge_data
                
            #     idle = False
            #     driver_locations_last_15_minutes = await fetch_from_table(session,
            #                                                                   DriverLocation,
            #                                                                   ["lat" , "lng"],
            #                                                                   [
            #                                                                     DriverLocation.driver_uuid == driver_uuid,
            #                                                                     DriverLocation.created_at >=before_15_min
            #                                                                   ],
            #                                                                   order_by ="-id"
            #                                                                   )
            #     locations_len = len(driver_locations_last_15_minutes)
            #     if locations_len > 3:
            #         first_half_distance = await haversine(driver_locations_last_15_minutes[0]["lat"] , driver_locations_last_15_minutes[0]["lng"] , driver_locations_last_15_minutes[locations_len//2]["lat"] , driver_locations_last_15_minutes[locations_len//2]["lng"])
            #         if first_half_distance < 50:
            #             second_half_distance = await haversine(driver_locations_last_15_minutes[locations_len//2]["lat"] , driver_locations_last_15_minutes[locations_len//2]["lng"] , driver_locations_last_15_minutes[-1]["lat"] , driver_locations_last_15_minutes[-1]["lng"])
            #             if second_half_distance < 50:
            #                 idle = True
                            
            #     if porter_trip_instance:
            #         if porter_trip_instance.trip_off_time == None:
            #             if idle:
            #                 nudge_data["title"] = "यात्रा से जुड़ी जानकारी"
            #                 nudge_data["message"] = "आप पिछले 15 मिनट से चल रही यात्रा के दौरान निष्क्रिय हैं, क्या आप ड्रॉप लोकेशन पर हैं?"
            #                 nudge_data["data"] = {
            #                     "screen_type" : "full",
            #                     "action_type" : "Trip Query",
            #                     "overlay_title" : "Are you at drop location",
            #                     "overlay_text" : "You are idle from last 15 minutes with ongoing trip , are you on drop location"
            #                 }
            #                 return nudge_data
            #             else:
            #                 return None
                        
                    
            #     if hotspot_instance:
            #         if hotspot_instance.reached_hotspot == False:
            #             eta = hotspot_instance.route_duration_seconds
            #             extended_eta = eta*2.5
            #             created_at = hotspot_instance.created_at
            #             time_diff_seconds = (today - created_at).total_seconds()
                        
            #             if time_diff_seconds >= extended_eta:
            #                 if idle:
            #                     nudge_data["title"] = "हॉटस्पॉट की ओर नहीं बढ़ रहे हैं"
            #                     nudge_data["message"] = f"आप उस हॉटस्पॉट की ओर नहीं बढ़ रहे हैं, जिसे आपने चुना था। क्या आप ड्रॉप लोकेशन पर हैं? अगर नहीं, तो कृपया हॉटस्पॉट पर पहुँचें।"
            #                     nudge_data["data"] = {
            #                         "screen_type" : "full",
            #                         "action_type" : "Hotspot Not Reached Before Extended ETA",
            #                         "overlay_title" : "Are you at pickup location",
            #                         "overlay_text" : f"You are not moving to hotspot you requested at {created_at} , are you at drop location"
            #                     }
            #                     nudge_data["image"] =  hotspot_reminder_banner_hindi
            #                     return nudge_data
                            
            #                 else:
            #                     nudge_data["title"] = "हॉटस्पॉट की ओर नहीं बढ़ रहे हैं"
            #                     nudge_data["message"] = f"आप उस हॉटस्पॉट की ओर बहुत धीरे बढ़ रहे हैं, जिसे आपने चुना था। क्या आप पिकअप के लिए जा रहे हैं? अगर नहीं, तो कृपया हॉटस्पॉट पर पहुँचें।"
            #                     nudge_data["data"] = {
            #                         "screen_type" : "full",
            #                         "action_type" : "Hotspot Not Reached Before Extended ETA",
            #                         "overlay_title" : "Are you going for pickup",
            #                         "overlay_text" : f"You are moving too slow to hotspot you requested at {created_at} , are you at going for pickup"
            #                     }
            #                     nudge_data["image"] =  hotspot_reminder_banner_hindi
            #                     return nudge_data
                        
                        

            #         else:
            #             reached_hotspot_timestamp = hotspot_instance.reached_hotspot_timestamp
            #             time_diff_minutes = (today - reached_hotspot_timestamp).total_seconds()/60
            #             if time_diff_minutes >=20:
            #                 driver_to_hotspot_distance = await haversine(driver_location.lat , driver_location.lng , hotspot_instance.end_lat , hotspot_instance.end_lng)
                            
            #                 if driver_to_hotspot_distance > 100:
            #                     if idle:
            #                         nudge_data["title"] = "हॉटस्पॉट रिमाइंडर"
            #                         nudge_data["message"] = "कृपया हॉटस्पॉट पर जाएं"
            #                         nudge_data["data"] = {
            #                             "screen_type" : "full",
            #                             "action_type" : "Hotspot Reminder",
            #                             "overlay_title" : "Go to Hotspot",
            #                             "overlay_text" : "You are standing away from hotspot , are you on Pickup? if not , Request a hotspot and reach hotspot"
            #                         }
            #                         nudge_data["image"] =  hotspot_reminder_banner_hindi
            #                         return nudge_data
            #                     else:
            #                         nudge_data["title"] = "हॉटस्पॉट रिमाइंडर"
            #                         nudge_data["message"] = "कृपया हॉटस्पॉट पर जाएं"
            #                         nudge_data["data"] = {
            #                             "screen_type" : "full",
            #                             "action_type" : "Hotspot Reminder",
            #                             "overlay_title" : "Go to Hotspot",
            #                             "overlay_text" : "You are running away from hotspot , are you going for  Pickup? if not , Request a hotspot and reach hotspot"
            #                         }
            #                         nudge_data["image"] =  hotspot_reminder_banner_hindi
            #                         return nudge_data
                            
            #                 else:
            #                     nudge_data["title"] = "हॉटस्पॉट रिमाइंडर"
            #                     nudge_data["message"] = "कृपया हॉटस्पॉट पर जाएं"
            #                     nudge_data["data"] = {
            #                         "screen_type" : "full",
            #                         "action_type" : "Hotspot Reminder",
            #                         "overlay_title" : "Go to Hotspot",
            #                         "overlay_text" : "Request a hotspot and reach hotspot"
            #                     }
            #                     nudge_data["image"] =  hotspot_reminder_banner_hindi
            #                     return nudge_data
                            
            #             else:
            #                 return None
                
                
                
            #     if idle:
            #         nudge_data["title"] = "हॉटस्पॉट रिमाइंडर"
            #         nudge_data["message"] = "कृपया हॉटस्पॉट पर जाएं"
            #         nudge_data["data"] = {
            #             "screen_type" : "full",
            #             "action_type" : "Hotspot Reminder",
            #             "overlay_title" : "Go to Hotspot",
            #             "overlay_text" : "Request a hotspot and reach hotspot"
            #         }
            #         nudge_data["image"] = hotspot_reminder_banner_hindi
            #         return nudge_data

            #     else:
            #         nudge_data["title"] = "हॉटस्पॉट रिमाइंडर"
            #         nudge_data["message"] = "आप बिना किसी हॉटस्पॉट या ट्रिप के चल रहे हैं, क्या आप हब या चार्जिंग स्टेशन की ओर जा रहे हैं? अगर नहीं, तो कृपया किसी हॉटस्पॉट पर जाएँ।"
            #         nudge_data["data"] = {
            #             "screen_type" : "full",
            #             "action_type" : "Moving Query",
            #             "overlay_title" : "Movement query",
            #             "overlay_text" : "You are moving without any hotspot or trip, are you moving to hub or charging station?"
            #         }
            #         nudge_data["image"] = hotspot_reminder_banner_hindi
            #         return nudge_data
    
           

async def process_vehicle(session , vehicle):
    try:
        driver_uuid = vehicle["driver_uuid"]
        driver_nudge = await get_driver_nudge(session , driver_uuid)
        if driver_nudge:
            token = driver_nudge["token"]
            title = driver_nudge["title"]
            message = driver_nudge["message"]
            data = driver_nudge["data"]
            image = driver_nudge.get("image" , None)
            send_fcm_notification(token , title , message , data , image)
            
        
    except Exception as e:
        print(f"Exception in processing vehicle {vehicle.get('vehicle_number', 'unknown')}: {e}")





async def monitor_for_nudges():
    
    while True:
        try:
            print("bot started")
            async for session in get_async_db():
                all_vehicles = await fetch_from_table(session , VehicleMain , None , {"assigned" : True , "is_enable" : True})
                tasks = [process_vehicle(session , vehicle) for vehicle in all_vehicles]
                await asyncio.gather(*tasks)
                await session.commit()
                await session.close()
        except Exception as e:
            print(f"An exception occured in nudges bot - str{e}")
            
        
        await asyncio.sleep(300)