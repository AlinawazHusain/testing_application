from pydantic import BaseModel
from typing import Any, Optional
from datetime import time

    


class get_vehicle_detail_request(BaseModel):
    vehicle_number : str

class get_vehicle_detail_response(BaseModel):
    owner_name : str|None
    vehicle_model : str|None
    fuel_type : str|None
    lender : str|None
    puc_upto : str|None
    insurance_upto : str|None
    fitness_upto : str|None
    rto : str|None




class add_vehicle_request(BaseModel):
    vehicle_number :str
    
    
    
class add_vehicle_response(BaseModel):
    vehicle_uuid : str



class update_vehicle_request(BaseModel):
    vehicle_uuid:str
    updates:dict

class update_vehicle_response(BaseModel):
    data:dict
    
    
class get_vehicle_data_request(BaseModel):
    vehicle_uuid :str


class get_vehicle_data_response(BaseModel):
    data:dict


class get_vehicle_docs_request(BaseModel):
    vehicle_uuid:str


class get_vehicle_docs_response(BaseModel):
    fitness_certificate :str|None
    rc :str|None
    puc : str|None
    permit : str|None
    insurance_docs : str|None
    

class update_vehicle_docs_response(BaseModel):
    file_path :str
    

class add_driver_to_vehicle_response(BaseModel):
    data:dict
    
class assign_driver_to_vehicle_request(BaseModel):
    vehicle_uuid:str
    driver_uuid: str
    
class assign_driver_to_vehicle_response(BaseModel):
    vehicle_uuid:str
    driver_uuid: str

class add_driver_to_vehicle_request(BaseModel):
    vehicle_uuid:str
    driver_uuid: str

    
class get_vehicle_assigned_data_request(BaseModel):
    vehicle_uuid:str






class vehicle_assigned_header(BaseModel):
    id:int
    vehicle_uuid:str
    vehicle_number : str
    vehicle_model : str
    vehilce_status:str
    vehilce_driver_current_status:str
    
    
class vehicle_assigned_driver(BaseModel):
    id :int
    driver_uuid:str
    driver_name:str|None
    driver_role:str
    driver_profile_image:str|None
    driver_country_code:str
    driver_phone_number:str
    driver_attendance_status:str
    driver_verification_status:bool
    
    
class vehicle_mapped_driver(BaseModel):
    id :int
    driver_uuid:str
    driver_name:str|None
    driver_role:str
    driver_profile_image:str|None
    driver_can_be_assigned:bool
    driver_verification_status:bool


class vehicle_cost_summary(BaseModel):
    monthly_vehicle_cost:float
    monthly_vehicle_utilization:str
    monthly_petty_expense:float
    
class vehicle_time_utilization(BaseModel):
    total_time_hr : float
    idle_time_hr : float
    earning_time : float

class vehicle_distance_utilization(BaseModel):
    total_distance_km : float
    idle_distance_km : float
    earning_distance_km : float
    
    
class vehicle_performance(BaseModel):
    time_utilization_monthly:vehicle_time_utilization
    distance_utilization_monthly:vehicle_distance_utilization
    time_utilization_today:vehicle_time_utilization
    distance_utilization_today:vehicle_distance_utilization
    
    
class vehicle_live_location(BaseModel):
    latitude:float
    longitude:float
    location_name:str|None
    updated_at:Any
    

class get_vehicle_assigned_data_soc_and_speed(BaseModel):
    vehicle_current_soc_percentage:float
    vehicle_km_left:float
    vehicle_speed_kmph:float
    
class get_vehicle_assigned_data_response(BaseModel):
    vehicle_assigned_header : vehicle_assigned_header
    assigned_driver : vehicle_assigned_driver|None
    other_mapped_driver : list[vehicle_mapped_driver]
    vehicle_soc_and_speed:get_vehicle_assigned_data_soc_and_speed|None
    vehicle_cost_summary : vehicle_cost_summary
    vehicle_performance : vehicle_performance
    vehicle_live_location : vehicle_live_location|None











class unassigned_vehicles(BaseModel):
    id:int
    vehicle_number:str
    vehicle_uuid:str
    vehicle_tag:str
    
    
class assigned_vehicles(BaseModel):
    id:int
    vehicle_number:str
    vehicle_uuid:str
    vehicle_fuel_type:str|None
    vehicle_status:str
    driver_uuid:str
    driver_name:str|None
    driver_profile_image:str|None
    driver_country_code:str
    driver_phone_number:str
    driver_verification_status:bool
    driver_role:str
    vehicle_other_drivers_number:int
    vehicle_current_activity:str

class get_all_vehicle_data_response(BaseModel):
    unassigned_vehicles:list[unassigned_vehicles]
    assigned_vehicles:list[assigned_vehicles]
    
    
    
    
    
    
    
class get_vehicle_costing_request(BaseModel):
    vehicle_uuid : str
    
    
class get_vehicle_costing_response(BaseModel):
    vehicle_emi : Optional[float] = 0.0
    parking_cost : Optional[float] = 0.0
    maintenance : Optional[float] = 0.0
    
    
class update_vehicle_costing_request(BaseModel):
    vehicle_uuid : str
    vehicle_emi : Optional[float] = None
    parking_cost : Optional[float] = None
    driver_salary : Optional[float] = None
    maintenance : Optional[float] = None

class update_vehicle_costing_response(BaseModel):
    updated : bool
    
    
    
class unassign_driver_from_vehicle_request(BaseModel):
    vehicle_uuid:str
    driver_uuid:str

class unassign_driver_from_vehicle_response(BaseModel):
    sucess_status:bool

    
class remove_driver_from_vehicle_request(BaseModel):
    vehicle_uuid:str
    driver_uuid:str

class remove_driver_from_vehicle_response(BaseModel):
    sucess_status:bool
    
    

class remove_driver_from_vehicle_request(BaseModel):
    vehicle_uuid:str
    driver_uuid:str
    
class remove_driver_from_vehicle_response(BaseModel):
    success_status:bool
    
class remove_vehicle_request(BaseModel):
    vehicle_uuid:str

    
class remove_vehicle_response(BaseModel):
    success_status:bool
    
    
    
    
    



class get_unassigned_vehicle_data_request(BaseModel):
    vehicle_uuid:str


class mapped_driver_data(BaseModel):
    id :int
    driver_uuid :str
    driver_name :str|None
    driver_role :str
    driver_profile_image :str|None
    driver_can_be_assigned :bool
    driver_verification_status :bool

class other_available_driver_data(BaseModel):
    id :int
    driver_uuid :str
    driver_name :str|None
    driver_profile_image :str|None
    driver_verification_status :bool


    
class get_unassigned_vehicle_data_response(BaseModel):
    assigned_driver : vehicle_assigned_driver|None
    mapped_drivers :list[mapped_driver_data]
    other_available_drivers : list[other_available_driver_data]

