from math import atan2, cos, radians, sin, sqrt
from sqlalchemy import desc, func
from db.database_operations import get_tuple_instance
from models.assignment_mapping_models import MfoVehicleMapping
from models.attendace_models import DriverAttendance
from models.can_data_model import CANData
from models.driver_models import DriverLocation
from models.hotspot_routes_models import HotspotRoutes
from models.porter_models import AvaronnPorterTrip
from models.vehicle_models import VehicleLocation, VehicleMain
from utils.time_utils import get_utc_time
from settings.static_data_settings import static_table_settings

async def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))




async def get_driver_activity(session , driver_uuid , mfo_uuid = None , vehicle_uuid = None):
    if mfo_uuid:
        mfo_vehicle_mapping = await get_tuple_instance(session , MfoVehicleMapping , {"mfo_uuid" : mfo_uuid , "current_assigned_driver" : driver_uuid , "is_enable" : True})
        driver_attendance_status = 'No action'
        if not mfo_vehicle_mapping:
            return [driver_attendance_status , "Driver not active - not marked present or no vehicle assigned."]
        
        vehicle_uuid = mfo_vehicle_mapping.vehicle_uuid
    
    attendance = await get_tuple_instance(
            session,
            DriverAttendance,
            {'driver_uuid': driver_uuid  , "vehicle_uuid" : vehicle_uuid},
            extra_conditions=[
                func.DATE(DriverAttendance.attendance_trigger_time) == func.DATE(get_utc_time())
            ],
            order_by=[desc(DriverAttendance.id)],
            limit=1  
        )
    
    attendance_states = static_table_settings.static_table_data["ATTENDANCE_STATES"]
    
    if attendance:
        attendance_status = attendance_states.get(attendance.attendance_state_uuid)
        if attendance_status == "No action":
            return [attendance_status ,"Driver not marked attendance yet "]
        
        elif attendance_status == "Absent":
            return [attendance_status , "Driver marked absent - not comming today "]
        
        elif attendance_status == "Expired":
            attendance_status = "Att. Expired"
            return [attendance_status , "Driver Attendance is expired "]
        
        else:
            vehicle_reached = attendance.bluetooth_connection_time != None
            
            if not vehicle_reached:
                return [attendance_status , "Driver marked present - have to reach the vehicle "]
            
            else:
                vehicle_main_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : vehicle_uuid , "is_enable" : True})
                vehicle_location = await get_tuple_instance(session ,
                                                            VehicleLocation , 
                                                            {"vehicle_number" : vehicle_main_instance.vehicle_number},
                                                            order_by=[desc(VehicleLocation.id)],
                                                            limit = 1
                                                            )
                if not vehicle_location:
                    return [attendance_status , "Driver Connected to vehicle - Integrate telematic for more updates"]
                
                driver_location = await get_tuple_instance(session, 
                                                           DriverLocation,
                                                           {"driver_uuid" : driver_uuid},
                                                           order_by=[desc(DriverLocation.id)],
                                                           limit = 1
                                                           )
                
                can_data = await get_tuple_instance(session ,
                                                    CANData ,
                                                    {"vehicle_number" : vehicle_main_instance.vehicle_number},
                                                    order_by=[desc(CANData.id)],
                                                    limit = 1
                                                    )
                ignition_on = vehicle_location.ignstatus == "on"
                vehicle_speed = can_data.vehicle_speed_value
                driver_to_vehicle_distance = await haversine(vehicle_location.lat , vehicle_location.lng , driver_location.lat , driver_location.lng)
                
                if vehicle_main_instance.vehicle_at_hub:
                    if driver_to_vehicle_distance > 30:
                        return [attendance_status , "Driver connected vehicle then go away."]
                    else:
                        if not ignition_on:
                            return [attendance_status ,"Trip assigned - waiting to begin at the hub"]
                        else:
                            return [attendance_status ,"Driver ready to go for trip ."]
                else:
                    driver_activity = [attendance_status , "Driver out of hub -  No actions"]
                    porter_trip_instance = await get_tuple_instance(session ,
                                                            AvaronnPorterTrip ,
                                                            {"driver_uuid" : driver_uuid} ,
                                                                extra_conditions=[
                                                            func.DATE(AvaronnPorterTrip.trip_on_time) == func.DATE(get_utc_time())
                                                            ],
                                                            order_by=[desc(AvaronnPorterTrip.id)] ,
                                                            limit = 1)
                    hotspot_instance = await get_tuple_instance(session , HotspotRoutes ,{"driver_uuid" : driver_uuid} , order_by=[desc(HotspotRoutes.id)] , limit = 1)
                    
                    if hotspot_instance and porter_trip_instance:
                        if hotspot_instance.created_at > porter_trip_instance.trip_on_time:
                            if hotspot_instance.reached_hotspot:
                                vehicle_to_hotspot_distance = await haversine(vehicle_location.lat , vehicle_location.lng , hotspot_instance.end_lat , hotspot_instance.end_lng)
                                if vehicle_to_hotspot_distance <50:
                                    driver_activity = [attendance_status , "Driver reached hotspot - waiting for order."]
                                else:
                                    if vehicle_speed > 1:
                                        driver_activity = [attendance_status ,"Driver probably moving for a pickup."]
                                    else:
                                        driver_activity = [attendance_status , "Driver probably on pickup location ."]
                                
                            else:
                                vehicle_to_hotspot_requested_location_distance = await haversine(vehicle_location.lat , vehicle_location.lng , hotspot_instance.start_lat , hotspot_instance.start_lng)
                                if vehicle_to_hotspot_requested_location_distance <30:
                                    if vehicle_speed > 1:
                                        driver_activity = [attendance_status , "Driver requested for hotspot and start moving "]
                                    else:
                                        driver_activity = [attendance_status , "Driver requested for hotspot - have to start moving"]
                                
                                else:
                                    hotspot_requested_to_current_time_gap = (get_utc_time() - hotspot_instance.created_at).total_seconds()
                                    time_over_eta = hotspot_requested_to_current_time_gap - hotspot_instance.route_duration_seconds
                                    
                                    if time_over_eta > 900:
                                        if vehicle_speed > 1:
                                            driver_activity = [attendance_status ,"Driver probably moving for pickup ."]
                                        else:
                                            driver_activity = [attendance_status , "Driver probably on pickup location ."]
                                    else:
                                        if vehicle_speed > 1:
                                            driver_activity = [attendance_status ,"Driver moving toward a hotspot"]
                                        else:
                                            driver_activity = [attendance_status ,"Driver stopped on way to hotspot"]
                                        
                        else:
                            vehicle_to_pickup_distance = await haversine(porter_trip_instance.trip_on_lat , porter_trip_instance.trip_on_lat , vehicle_location.lat , vehicle_location.lng)
                            if not porter_trip_instance.trip_off_time:
                                if vehicle_speed > 1:
                                    driver_activity = [attendance_status , "Trip in progress - driving to delivery location."]
                                else:
                                    if vehicle_to_pickup_distance <20:
                                        driver_activity = [attendance_status , "Driver didn't moved from pickup location yet . "]
                                    else:
                                        driver_activity = [attendance_status , "Driver Stopped during trip - unschedule stop"]
                            
                            else:
                                vehicle_to_dropoff_distance = await haversine(porter_trip_instance.trip_off_lat , porter_trip_instance.trip_off_lat , vehicle_location.lat , vehicle_location.lng)
                                drop_time_to_current_time_gap = (get_utc_time() - porter_trip_instance.trip_off_time).total_seconds()
                                if vehicle_speed > 1:
                                    driver_activity = [attendance_status , "Driver completed a trip probably moving somewhere"]
                                else:
                                    if vehicle_to_dropoff_distance <20:
                                        driver_activity = [attendance_status , f"Driver is on drop location from {drop_time_to_current_time_gap//60} minutes"]
                                    else:
                                        driver_activity = [attendance_status , f"Driver dropped last order {drop_time_to_current_time_gap//60} minutes ago."]
                                        
                    
                    
                    if hotspot_instance and not porter_trip_instance:
                        if hotspot_instance.reached_hotspot:
                            vehicle_to_hotspot_distance = await haversine(vehicle_location.lat , vehicle_location.lng , hotspot_instance.end_lat , hotspot_instance.end_lng)
                            if vehicle_to_hotspot_distance <30:
                                driver_activity = [attendance_status , "Driver reached hotspot - waiting for order."]
                            else:
                                if vehicle_speed > 1:
                                    driver_activity = [attendance_status , "Driver probably moving for a pickup."]
                                else:
                                    driver_activity = [attendance_status , "Driver probably on pickup location ."]
                            
                        else:
                            vehicle_to_hotspot_requested_location_distance = await haversine(vehicle_location.lat , vehicle_location.lng , hotspot_instance.start_lat , hotspot_instance.start_lng)
                            if vehicle_to_hotspot_requested_location_distance <30:
                                if vehicle_speed > 1:
                                    driver_activity = [attendance_status , "Driver requested for hotspot and start moving "]
                                else:
                                    driver_activity = [attendance_status , "Driver requested for hotspot - have to start moving"]
                            
                            else:
                                hotspot_requested_to_current_time_gap = (get_utc_time() - hotspot_instance.created_at).total_seconds()
                                time_over_eta = hotspot_requested_to_current_time_gap - hotspot_instance.route_duration_seconds
                                
                                if time_over_eta > 900:
                                    if vehicle_speed > 1:
                                        driver_activity = [attendance_status , "Driver probably moving for pickup ."]
                                    else:
                                        driver_activity = [attendance_status , "Driver probably on pickup location ."]
                                else:
                                    if vehicle_speed > 1:
                                        driver_activity = [attendance_status ,"Driver moving toward a hotspot"]
                                    else:
                                        driver_activity = [attendance_status , "Driver stopped on way to hotspot"]
                            
                    
                    if porter_trip_instance and not hotspot_instance:
                        vehicle_to_pickup_distance = await haversine(porter_trip_instance.trip_on_lat , porter_trip_instance.trip_on_lat , vehicle_location.lat , vehicle_location.lng)
                        if not porter_trip_instance.trip_off_time:
                            if vehicle_speed > 1:
                                driver_activity = [attendance_status , "Trip in progress - driving to delivery location."]
                            else:
                                if vehicle_to_pickup_distance <20:
                                    driver_activity = [attendance_status , "Driver didn't moved from pickup location yet . "]
                                else:
                                    driver_activity = [attendance_status ,"Driver Stopped during trip - unschedule stop"]
                        
                        else:
                            vehicle_to_dropoff_distance = await haversine(porter_trip_instance.trip_off_lat , porter_trip_instance.trip_off_lat , vehicle_location.lat , vehicle_location.lng)
                            drop_time_to_current_time_gap = (get_utc_time() - porter_trip_instance.trip_off_time).total_seconds()
                            if vehicle_speed > 1:
                                driver_activity = [attendance_status , "Driver completed a trip probably moving somewhere"]
                            else:
                                minutes = drop_time_to_current_time_gap//60
                                time_status = f"{minutes} minutes"
                                if minutes >= 60:
                                    hour = minutes//60
                                    minutes = minutes%60
                                    time_status = f"{hour}:{minutes} hour"
                                    
                                if vehicle_to_dropoff_distance <20:
                                    driver_activity = [attendance_status ,f"Driver is on drop location from {time_status}"]
                                else:
                                    driver_activity = [attendance_status , f"Driver dropped last order {time_status} ago."]
                        
                    return driver_activity 
                    
    return [driver_attendance_status , "No action now"]