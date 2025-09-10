from typing import Any
from pydantic import BaseModel


class porter_trip_on_request(BaseModel):
    driver_lat : float
    driver_lng : float

class porter_trip_on_response(BaseModel):
    avaronn_porter_trip_uuid : str
    points_earned:int


class porter_trip_off_request(BaseModel):
    avaronn_porter_trip_uuid : str
    driver_lat : float
    driver_lng : float

class porter_trip_off_response(BaseModel):
    trip_on_time : Any 
    trip_off_time : Any
    total_trip_time : Any
    points_earned:int
    incentive_earned : float
    
    
class get_porter_trip_response(BaseModel):
    current_trip : dict|None
    completed_trips : list[dict]
    
    