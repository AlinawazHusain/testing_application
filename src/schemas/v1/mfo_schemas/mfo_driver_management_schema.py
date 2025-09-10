from pydantic import BaseModel
from typing import Any, Optional

class register_or_add_driver_request(BaseModel):
    country_code:str
    driver_phone_number:str

class register_or_add_driver_response(BaseModel):
    request_id:str
    
class verify_and_add_driver_request(BaseModel):
    country_code: str
    driver_phone_number:str
    driver_name : str
    otp: str
    request_id:str
    vehicle_uuid: Optional[str] = None
    
class verify_and_add_driver_response(BaseModel):
    driver_uuid : str
    driver_name : str|None
    driver_profile_image : str|None
    driver_verification_status : bool
    

class unassigned_driver(BaseModel):
    id : int
    driver_uuid : str
    driver_name : str|None
    driver_profile_image : str|None
    driver_country_code:str
    driver_phone_number:str
    driver_verification_status : bool
    driver_tag : str
    

class assigned_driver(BaseModel):
    id : int
    driver_uuid : str
    driver_name : str|None
    driver_profile_image : str|None
    driver_country_code : str
    driver_phone_number : str
    driver_verification_status : bool
    driver_status:str
    vehicle_uuid:str
    vehicle_number:str
    driver_current_activity:str
    driver_role:str
    driver_tag : str
    
    
class get_all_drivers_response(BaseModel):
    unassigned_drivers : list[unassigned_driver]
    assigned_drivers : list[assigned_driver]
    
    
    



class get_driver_profile_request(BaseModel):
    driver_uuid : str
    
    
class get_driver_profile_app_bar(BaseModel):
    driver_name:str|None
    driver_status:str
    driver_country_code:str
    driver_phone_number:str
    driver_current_activity:str
    
class get_driver_profile_driver_card(BaseModel):
    driver_name:str|None
    driver_verification_status:bool
    driver_score:float
    driver_years_of_experience:float
    driver_distance_drivern_km:float
    driver_task_completed : int
    
class get_driver_profile_assigned_vehicle(BaseModel):
    vehicle_uuid:str|None
    vehicle_number:str|None
    
class get_driver_profile_other_mapped_vehicle(BaseModel):
    vehicle_uuid:str
    vehicle_number:str
    mapped_driver_name:str|None
    vehicle_status:str|None
    
class get_driver_profile_monthly_salary_and_expense(BaseModel):
    driver_monthly_salary: Optional[float] = 0.0
    driver_petty_expense: Optional[float] = 0.0
    

class driver_time_utilization(BaseModel):
    total_time_hr : float
    idle_time_hr : float
    earning_time : float

class driver_distance_utilization(BaseModel):
    total_distance_km : float
    idle_distance_km : float
    earning_distance_km : float
    
class get_driver_profile_driver_performance(BaseModel):
    time_utilization_monthly:driver_time_utilization
    distance_utilization_monthly:driver_distance_utilization
    time_utilization_today:driver_time_utilization
    distance_utilization_today:driver_distance_utilization
    
    
class get_driver_profile_driver_incentive_programme_summary(BaseModel):
    incentive_summary : dict
    
    
class get_driver_profile_driver_sla_policy(BaseModel):
    updated_at:Any
    
class get_driver_profile_driver_attendance_summary(BaseModel):
    present_count : Optional[int] = 0
    absent_count : Optional[int] = 0
    
    
class get_driver_profile_driver_work_summary_and_policy(BaseModel):
    driver_incentive_programme_summary : get_driver_profile_driver_incentive_programme_summary|None
    driver_sla_policy : get_driver_profile_driver_sla_policy
    driver_attendance_summary : get_driver_profile_driver_attendance_summary


class get_driver_profile_driver_location(BaseModel):
    driver_lat : float
    driver_lng : float
    driver_location:str
    
    
class get_driver_profile_response(BaseModel):
    app_bar : get_driver_profile_app_bar
    driver_profile : get_driver_profile_driver_card
    assigned_vehicle: get_driver_profile_assigned_vehicle
    other_mapped_vehicles : list[get_driver_profile_other_mapped_vehicle]
    monthly_salary_and_expense : get_driver_profile_monthly_salary_and_expense
    work_summary_and_policy : get_driver_profile_driver_work_summary_and_policy
    performance_insight : get_driver_profile_driver_performance
    driver_location : get_driver_profile_driver_location|None
    
    
    
    

class get_unassigned_driver_data_request(BaseModel):
    driver_uuid:str
    
    
class assigned_vehicle(BaseModel):
    vehicle_uuid:str
    vehicle_number:str
    driver_name:str|None
    vehicle_model:str|None
    vehicle_fuel_type:str
    
class mapped_vehicle(BaseModel):
    vehicle_uuid:str
    vehicle_number:str
    driver_name:str|None
    vehicle_model:str|None
    vehicle_fuel_type:str
    can_be_assigned:bool

class other_available_vehicle(BaseModel):
    vehicle_uuid:str
    vehicle_number:str
    driver_name:str|None
    vehicle_model:str|None
    vehicle_fuel_type:str|None
    
    
class get_unassigned_driver_data_response(BaseModel):
    assigned_vehicle :assigned_vehicle|None
    mapped_vehicles : list[mapped_vehicle]
    other_available_vehicles : list[other_available_vehicle]
    
    
    
    
    
class assign_driver_for_future_request(BaseModel):
    driver_uuid : str
    vehicle_uuid : str
    start_day : int
    start_month:int
    start_year : int
    end_day : int
    end_month:int
    end_year : int
    
    
class assign_driver_for_future_response(BaseModel):
    driver_uuid:str
    vehicle_uuid:str
    start_date:Any
    end_date:Any
    
    
class get_driver_docs_response(BaseModel):
    aadhar_card : str|None
    pan_card :str|None
    driving_license : str|None 
    aadhar_card_back : str|None

class get_driver_docs_request(BaseModel):
    driver_uuid : str
    

class update_driver_salary_request(BaseModel):
    driver_uuid:str
    driver_salary:float
class update_driver_salary_response(BaseModel):
    driver_uuid:str
    driver_salary:float

class remove_driver_request(BaseModel):
    driver_uuid:str
    
    
class remove_driver_response(BaseModel):
    success_status:bool