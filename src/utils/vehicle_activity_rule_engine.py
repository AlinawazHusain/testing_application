from math import atan2, cos, radians, sin, sqrt
from sqlalchemy import desc, func
from db.database_operations import get_tuple_instance
from models.attendace_models import DriverAttendance
from models.can_data_model import CANData
from models.driver_models import DriverLocation
from models.vehicle_models import VehicleLocation, VehicleMain
from settings.static_data_settings import static_table_settings
from utils.time_utils import get_utc_time



async def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))



async def get_inactive_vehicle_activity(session , vehicle_uuid , vehicle_number ,vehicle_at_hub):
    vehicle_location_isntance = await get_tuple_instance(session ,
                                                    VehicleLocation ,
                                                    {"vehicle_number" : vehicle_number},
                                                    order_by=[desc(VehicleLocation.id)],
                                                    limit = 1
                                                    )
    ignition_on_status = False
    have_location_data = False
    if vehicle_location_isntance:
            ignition_on_status = vehicle_location_isntance.ignstatus == "on"
            have_location_data = True
            
    
    if vehicle_at_hub and have_location_data:
        if not ignition_on_status:
            return "Vehicle inactive - no active driver or task"
        
        if ignition_on_status:
            return "Soft alert! - no active driver but ignition is on"
    
    if have_location_data and not vehicle_at_hub:
        if ignition_on_status:
            return "Hard alert! - Vehicle is running out of hub without any active driver"
        
        if not ignition_on_status:
            return "Hard alert! - Vehicle is idle out of hub without any active driver"
        
    if not have_location_data:
        return "Vehicle inactive - no driver or task , integrate telematics for better updates"
        
    return "No Data available at this instance"
            
            
            
            
            
            
            
            
async def get_idle_vehicle_activity(session , vehicle_uuid , vehicle_number ,vehicle_at_hub , driver_uuid):
    vehicle_activity = "Driver assigned but absent - attendance not marked"
    
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
    
    # driver_location_instance = await get_tuple_instance(session , 
    #                                                     DriverLocation ,
    #                                                     {"driver_uuid" : driver_uuid} ,
    #                                                     order_by=[desc(DriverLocation.id)],
    #                                                     limit = 1
    #                                                     )
    
    vehicle_location_instance = await get_tuple_instance(session ,
                                                    VehicleLocation ,
                                                    {"vehicle_number" : vehicle_number},
                                                    order_by=[desc(VehicleLocation.id)],
                                                    limit = 1
                                                    )
    ignition_on_status = False
    have_location_data = False
    if vehicle_location_instance:
            ignition_on_status = vehicle_location_instance.ignstatus == "on"
            have_location_data = True
            
    
    if attendance:
        if attendance.attendance_time:
            if attendance.bluetooth_connection_time:
                if have_location_data:
                    if vehicle_at_hub:
                        if ignition_on_status:
                            vehicle_activity = "Vehicle started - ready to leave the hub."
                            
                        if not ignition_on_status:
                            vehicle_activity = "Trip assigned - vehicle idle at hub."
                            
                    else:
                        # driver_to_vehicle_distance = await haversine(vehicle_location_instance.lat , vehicle_location_instance.lng , driver_location_instance.lat , driver_location_instance.lng)
                        # if driver_to_vehicle_distance > 30:
                        #     vehicle_activity = "Driver away from vehicle - unscheduled stop"
                        # else:
                        vehicle_activity = "Idle on route - stopped during task."
                                
                else:
                    vehicle_activity = "No Data Available - Integrate telematics for better updates"
            else:
                if vehicle_at_hub:
                    vehicle_activity = "Vehicle at hub and waiting for driver to connect"
                else:
                    vehicle_activity = "Vehicle outside the hub and waiting for driver to connect"
    
    
    return vehicle_activity




async def get_running_vehicle_activity(session , vehicle_uuid , vehicle_number ,vehicle_at_hub , driver_uuid):
    # driver_location_instance = await get_tuple_instance(session , 
    #                                                     DriverLocation ,
    #                                                     {"driver_uuid" : driver_uuid} ,
    #                                                     order_by=[desc(DriverLocation.id)],
    #                                                     limit = 1
    #                                                     )
    
    # vehicle_location_instance = await get_tuple_instance(session ,
    #                                                 VehicleLocation ,
    #                                                 {"vehicle_number" : vehicle_number},
    #                                                 order_by=[desc(VehicleLocation.id)],
    #                                                 limit = 1
    #                                                 )
     
    # driver_to_vehicle_distance = await haversine(vehicle_location_instance.lat , vehicle_location_instance.lng , driver_location_instance.lat , driver_location_instance.lng)
    
    # if driver_to_vehicle_distance > 20:
    #     vehicle_activity = "Vehicle is running but driver is away - someone else is running vehicle probably"
    # else:
    if vehicle_at_hub:
        vehicle_activity = "Vehicle is started and moving out from hub ."
    
    else:
            vehicle_activity = "Vehicle on active trip -en route ."
            
    
    return vehicle_activity
            
            
            
async def get_vehile_activity(session , vehicle_uuid):
    
    vehicle_main_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : vehicle_uuid , "is_enable" : True})
    vehicle_status_dict = static_table_settings.static_table_data["VEHICLE_STATUS"]
    
    vehicle_status = vehicle_status_dict.get(vehicle_main_instance.vehicle_status , None)
    
    if vehicle_status == "Inactive":
        vehicle_activity = await get_inactive_vehicle_activity(session , vehicle_uuid , vehicle_main_instance.vehicle_number , vehicle_main_instance.vehicle_at_hub)
        return vehicle_activity
    
    
    elif vehicle_status == "Idle":
                
        vehicle_can_instance = await get_tuple_instance(session , 
                                                        CANData ,
                                                        {"vehicle_number" :  vehicle_main_instance.vehicle_number},
                                                        order_by=[desc(CANData.id)],
                                                        limit =1
                                                        )
        if vehicle_can_instance:
            if vehicle_can_instance.soc_value < 25:
                vehicle_activity = f"SOC alert! - vehicle idle with low SOC - soc value : {vehicle_can_instance.soc_value}"
                return vehicle_activity
        elif not vehicle_can_instance:
            return "Telematics not integrated - integrate for better updates"
            
        vehicle_activity = await get_idle_vehicle_activity(session , vehicle_uuid , vehicle_main_instance.vehicle_number , vehicle_main_instance.vehicle_at_hub , vehicle_main_instance.driver_uuid)
        return vehicle_activity
    
    
    elif vehicle_status == "Running":
        
        vehicle_can_instance = await get_tuple_instance(session , 
                                                        CANData ,
                                                        {"vehicle_number" :  vehicle_main_instance.vehicle_number},
                                                        order_by=[desc(CANData.id)],
                                                        limit =1
                                                        )
        if vehicle_can_instance:
            if vehicle_can_instance.soc_value < 25:
                vehicle_activity = f"SOC alert! - vehicle running with low SOC - soc value : {vehicle_can_instance.soc_value}"
                return vehicle_activity
        elif not vehicle_can_instance:
            return "Telematics not integrated - integrate for better updates"
            
        vehicle_activity = await get_running_vehicle_activity(session , vehicle_uuid , vehicle_main_instance.vehicle_number , vehicle_main_instance.vehicle_at_hub , vehicle_main_instance.driver_uuid)
        return vehicle_activity
    
    