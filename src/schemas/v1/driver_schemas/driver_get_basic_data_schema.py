from pydantic import BaseModel
from typing import Any, Optional


class get_profile_data_response(BaseModel):
    name : str|None
    country_code:str
    phone_number:str
    profile_image : Optional[str] = None
    years_of_experience : Optional[Any] = None
    city : Optional[str] = None
    pincode : Optional[str] = None
    used_ev_before : bool
    distance_driven : float |None
    score : float|None
    assignments_completed : int
    verification_status : bool
    main_profile_completion_percentage : float
    docs_completion_percentage : float
    
    mfo_name: str|None
    mfo_country_code :str|None
    mfo_phone_number:str|None
    business_logo:str|None
    business_name : str|None
    

class get_docs_data_response(BaseModel):
    aadhar_card : Optional[str] = None
    pan_card : Optional[str] = None
    driving_license : Optional[str] = None
    aadhar_card_back : Optional[str] = None
    docs_completion_percentage : float
    
    
class get_vehicle_data_response(BaseModel):
    vehicle_data : list
    current_assigned_vehicle_details : dict
    present_status : bool
    

    
class SOS_response(BaseModel):
    mfo_phone_number : str | None
    
    
class pushNotification_request(BaseModel):
    notification_data:dict
    

class pushNotification_response(BaseModel):
    success:Optional[bool] = True