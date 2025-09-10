from datetime import datetime, time, timedelta
from os import getenv
from dotenv import load_dotenv
from sqlalchemy import desc, func
from db.database_operations import get_tuple_instance, insert_into_table
from integrations.attestr import get_vehicle_data
from integrations.aws_utils import write_json_to_s3
from models.assignment_mapping_models import MfoVehicleMapping
from models.attendace_models import DriverAttendance
from models.client_models import ClientMain
from models.hotspot_routes_models import HotspotRoutes
from models.porter_models import AvaronnPorterTrip
from models.task_management_models import Schedules, TaskScheduleMapping, Tasks
from models.vehicle_models import VehicleMain
from utils.data_read_utils import get_json_from_url
from settings.static_data_settings import static_table_settings
from utils.time_utils import convert_utc_to_ist, get_utc_time



load_dotenv()




async def get_vehicle_details(vehicle_number:str):
    """
    This function takes vehicle number as argument and returns its details
    First it check if details available in S3 bucket if not then 
    it fetches them from Attestr API using get vehicle details function and store in S3

    Args:
        vehicle_number (str): vehicle number for which this function fetch details

    Raises:
        e: Internal server Error if any

    Returns:
        data (dict): A dictionary of vehicle details.
    """
    try:
        s3_key = f"vehicle_details/{vehicle_number}.json"
        path_to_s3 = f"https://{getenv('FILE_UPLOAD_BUCKET')}.s3.{getenv('AWS_REGION')}.amazonaws.com/{s3_key}"
        vehicle_details = await get_json_from_url(path_to_s3)
        if not vehicle_details:
            vehicle_details = await get_vehicle_data(vehicle_number)
            path_to_s3 = await write_json_to_s3(vehicle_details , s3_key)
            
        data = {}
        data['owner_name'] = vehicle_details.get('owner' , 'unknown')
        data['vehicle_model'] = vehicle_details.get('makerModel' , "unknown")
        data['fuel_type'] = vehicle_details['fuelType']
        data['lender'] = vehicle_details['lender']
        data['puc_upto'] = vehicle_details['pollutionCertificateUpto']
        data['insurance_upto'] = vehicle_details['insuranceUpto']
        data['fitness_upto'] = vehicle_details['fitnessUpto']
        data['rto'] = vehicle_details['rto']
        data['category'] =  vehicle_details['category']
        data['financed'] =  vehicle_details.get('financed' , False)
        data['commercial'] =  vehicle_details.get('commercial' , False)
        return data , path_to_s3
    
    except Exception as e:
        raise e
    
    

async def create_avaronn_schedule_and_task(session , mfo_uuid:str , vehicle_uuid:str):
    
    client = await get_tuple_instance(session , ClientMain , {"name" : "Avaronn"})
    model_types_uuid_dict = static_table_settings.static_table_data['MODEL_TYPES']
    model_type_uuid = next((k for k , v in model_types_uuid_dict.items() if v == "Onspot") , None)   
    
    sub_model_types_uuid_dict = static_table_settings.static_table_data['SUB_MODEL_TYPES']
    sub_model_type_uuid = next((k for k , v in sub_model_types_uuid_dict.items() if v == "Porter") , None)     
    
    schedule_start_time =  time(9, 30, 0)
    schedule_start_time = (datetime.combine(datetime.today(), schedule_start_time) - timedelta(hours=5 , minutes = 30)).time()
    working_hours = 9
    
    schedule_data = {
        "client_uuid" : client.client_uuid,
        "mfo_driver_assignment_model" : model_type_uuid,
        "schedule_start_time": schedule_start_time,
        "schedule_end_time" : (datetime.combine(datetime.today(), schedule_start_time) + timedelta(hours=working_hours)).time()
        
    }
    schedule_instance = await  insert_into_table(session ,Schedules ,schedule_data)
    
    task_data = {
        "mfo_uuid" : mfo_uuid,
        "model_type" : model_type_uuid,
        "sub_model_type" : sub_model_type_uuid
    }
            
    task_status_dict = static_table_settings.static_table_data['TASK_STATUS']
    task_status_uuid = next((k for k , v in task_status_dict.items() if v == "Pending"))
        
    task_data["vehicle_uuid"] = vehicle_uuid
    task_data["task_start_time"] = get_utc_time()
    task_data["task_end_time"] = get_utc_time()
    task_data["task_status_uuid"] = task_status_uuid
    
    task_instance = await insert_into_table(session  , Tasks , task_data)
    
    task_schedule_mapping_instance = await insert_into_table(session , TaskScheduleMapping , {"task_uuid" : task_instance.task_uuid , "schedule_uuid" : schedule_instance.schedule_uuid})
    
    return





async def get_vehicle_tag(session , vehicle_uuid):
    vehicle_mfo_mapping_instance = await get_tuple_instance(session ,
                                                            MfoVehicleMapping ,
                                                            {"vehicle_uuid" : vehicle_uuid , "is_enable" : True},
                                                            order_by = [desc(MfoVehicleMapping.id)],
                                                            limit = 1
                                                            )
    driver_mapped_count = -1
    
    driver_roles_columns = ["primary_driver" , "secondary_driver" , "tertiary1_driver" , "tertiary2_driver" , "supervisor_driver"]
    if not vehicle_mfo_mapping_instance.current_assigned_driver:
        driver_mapped_count = 0
        
    
    for column in driver_roles_columns:
        value = getattr(vehicle_mfo_mapping_instance, column, None)
        if value:
            driver_mapped_count += 1
            
    vehicle_tag = f"+{driver_mapped_count} drivers" if driver_mapped_count>0 else "No driver"
    return [driver_mapped_count , vehicle_tag]





async def get_vehicle_current_activity(session , vehicle_status , vehicle_uuid , driver_uuid ):

    vehicle_current_activity = "Unable to get any activity"
    if vehicle_status == "Inactive":
        vehicle_current_activity = "Unable to get any activity"
    
    
    elif vehicle_status == "Under Maintenance":
        vehicle_current_activity = "Unable to get any activity"
        
        
    elif vehicle_status == "Idle":
        attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
        attendance_instance = await get_tuple_instance(
                        session,
                        DriverAttendance,
                        {'vehicle_uuid': vehicle_uuid},
                        extra_conditions=[
                            func.DATE(convert_utc_to_ist(DriverAttendance.attendance_trigger_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
                        ],
                        order_by=[desc(DriverAttendance.id)],
                        limit=1  
                    )
        if attendance_instance:
            driver_status = attendance_states_dict[attendance_instance.attendance_state_uuid]
        match driver_status:
            case "Present":
                if attendance_instance.bluetooth_connection_time:
                    vehicle_current_activity = "Driver connected to vehicle"
                    porter_trip_instance = await get_tuple_instance(session ,
                                                                    AvaronnPorterTrip ,
                                                                    {"vehicle_uuid" : vehicle_uuid} ,
                                                                    extra_conditions=[
                                                                    func.DATE(convert_utc_to_ist(AvaronnPorterTrip.trip_on_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
                                                                    ],
                                                                    order_by=[desc(AvaronnPorterTrip.id)] ,
                                                                    limit = 1)
                    if porter_trip_instance:
                        if not porter_trip_instance.trip_off_time:
                            vehicle_current_activity = "Vehicle is on trip "
                        else:
                            vehicle_current_activity = "Waiting for order at drop location"
                    hotspot_instance = await get_tuple_instance(session , HotspotRoutes ,{"driver_uuid" : driver_uuid} , order_by=[desc(HotspotRoutes.id)] , limit = 1)
                    if hotspot_instance:
                        if hotspot_instance.reached_hotspot:
                            if not hotspot_instance.got_trip:
                                vehicle_current_activity = f"Waiting for order on hotspot"
                        else:
                            vehicle_current_activity = f"Vehicle moving to  hotspot"
                else:
                    vehicle_current_activity = "Vehicle parked at hub & Awaiting driver to connect"
            case _:
                vehicle_current_activity = "Vehicle parked at hub & Awaiting attendance"
                
    
    
    elif vehicle_status == "Running":
        attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
        
        porter_trip_instance = await get_tuple_instance(session ,
                                                        AvaronnPorterTrip ,
                                                        {"vehicle_uuid" : vehicle_uuid} ,
                                                        extra_conditions=[
                                                        func.DATE(convert_utc_to_ist(AvaronnPorterTrip.trip_on_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
                                                        ],
                                                        order_by=[desc(AvaronnPorterTrip.id)] ,
                                                        limit = 1)
        if porter_trip_instance:
            if not porter_trip_instance.trip_off_time:
                vehicle_current_activity = "Vehicle is on trip "
            else:
                vehicle_current_activity = "Waiting for order at drop location"
        hotspot_instance = await get_tuple_instance(session , HotspotRoutes ,{"driver_uuid" : driver_uuid} , order_by=[desc(HotspotRoutes.id)] , limit = 1)
        if hotspot_instance:
            if hotspot_instance.reached_hotspot:
                if not hotspot_instance.got_trip:
                    vehicle_current_activity = f"Waiting for order on hotspot"
            else:
                vehicle_current_activity = f"Vehicle moving to hotspot"

    
    return vehicle_current_activity