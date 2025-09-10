from pydantic import BaseModel
from typing import Any, List, Optional
from datetime import date , datetime



class driver_updates(BaseModel):
    event_type:str
    event_uuid:str
    driver_name:str|None
    driver_profile_image:str|None
    driver_uuid:str
    driver_country_code:str
    driver_phone_number:str
    vehicle_uuid:str|None
    vehicle_number:str|None
    start_date:Any
    end_date:Any 
    event_status:str
    event_text:str
    had_action:bool
    update_timestamp:Any

class get_driver_updates_response(BaseModel):
    driver_updates : list[driver_updates]
 
 
 
class approve_driver_update_request(BaseModel):
    event_type : str
    event_uuid:str
    
class approve_driver_update_response(BaseModel):
    approve_status : str
    
    
class reject_driver_update_request(BaseModel):
    event_type : str
    event_uuid:str
    
class reject_driver_update_response(BaseModel):
    approve_status : str
    
    

class LeaveDetail(BaseModel):
    """
    Represents a single leave record for a driver.
    """
    
    leave_request_uuid: str
    start_date: date
    end_date: date
    leave_type: str
    reason: Optional[str] = None
    leave_status: str
    requested_at: datetime


class DriverLeave(BaseModel):
    """
    Contains all leave records for a specific driver.
    """
    
    driver_uuid: str
    leaves: List[LeaveDetail]


class GetLeaveRequestsResponse(BaseModel):
    """
    Response model for retrieving leave requests for multiple drivers.
    """
    
    drivers: List[DriverLeave]



class ApproveLeaveRequestRequest(BaseModel):
    """
    Request model for approving a leave request by mfo
    leave_request_uuid is  mapped leave request 
    refering to database table row unique identifier.
    """
    
    leave_request_uuid:str
    

class ApproveLeaveRequestResponse(BaseModel):
    """
    Response model after approving a leave request by mfo.
    """
    
    leave_request_uuid: str
    start_date: date
    end_date: date
    leave_type: str
    reason: Optional[str]
    leave_status_uuid: str
    requested_at: datetime
    
    
    
class RejectLeaveRequestRequest(BaseModel):
    """
    Request model for rejecting a leave request by mfo
    leave_request_uuid is  mapped leave request 
    refering to database table row unique identifier.
    """
    
    leave_request_uuid:str
    
    
    
class RejectLeaveRequestResponse(BaseModel):
    """
    Response model after rejecting a leave request by mfo.
    """
    
    leave_request_uuid: str
    start_date: date
    end_date: date
    leave_type: str
    reason: Optional[str] = None
    leave_status_uuid: str
    requested_at: datetime
    
    
    
    




class WorkOnOffDaysDetails(BaseModel):
    """
    Represents a single work on off day request record for a driver.
    """
    
    work_on_off_day_request_uuid: str
    off_date: date
    reason: Optional[str] = None
    request_status_uuid: str
    requested_at: datetime


class DriverWorkOnOffDays(BaseModel):
    """
    Contains all work on off day request records for a specific driver.
    """
    
    driver_uuid: str
    work_requests: List[WorkOnOffDaysDetails]


class GetWorkOnOffDayRequestsResponse(BaseModel):
    """
    Response model for retrieving  work on off day requests
    for multiple drivers.
    """
    
    drivers: List[DriverWorkOnOffDays]
    
    
    
    

class ApproveWorkOnOffDayRequestRequest(BaseModel):
    """
    Request model for approving a work on off day request
    by mfo work_on_off_day_request_uuid is  mapped 
    work on off day request refering to database 
    table row unique identifier.
    """
    
    work_on_off_day_request_uuid: str



class ApproveWorkOnOffDayRequestResponse(BaseModel):
    """
    Response model after approving a 
    work on off day request by mfo.
    """
    
    work_on_off_day_request_uuid: str
    off_date: date
    reason: Optional[str] = None
    request_status: str
    requested_at: datetime



class RejectWorkOnOffDayRequestRequest(BaseModel):
    """
    Request model for rejecting a work on off day request
    by mfo work_on_off_day_request_uuid is  mapped 
    work on off day request refering to database 
    table row unique identifier.
    """
    
    work_on_off_day_request_uuid: str



class RejectWorkOnOffDayRequestResponse(BaseModel):
    """
    Response model after rejecting a 
    work on off day request by mfo.
    """
    
    work_on_off_day_request_uuid: str
    off_date: date
    reason: Optional[str] = None
    request_status: str
    requested_at: datetime