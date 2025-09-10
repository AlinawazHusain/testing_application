from typing import Any, Optional
from pydantic import BaseModel
from datetime import datetime


class mark_present_request(BaseModel):
    driver_lat : float
    driver_lng : float


class mark_present_response(BaseModel):
    marked : bool
    points_earned:int
    

class mark_absent_request(BaseModel):
    driver_lat : float
    driver_lng : float


class mark_absent_response(BaseModel):
    marked : bool


class get_attendance_status_response(BaseModel):
    have_attendance_status: bool
    attendance_mark_time : Optional[Any] = None
    attendance_status : Optional[str] = None
    

class bluetooth_connected_request(BaseModel):
    driver_lat : float
    driver_lng : float
    
class bluetooth_connected_response(BaseModel):
    connected : bool
    points_earned : int
    
    
class have_attendance_response(BaseModel):
    have_attendance : bool
    
class request_new_attendance_response(BaseModel):
    requested : bool
    reason: str = ""
    

