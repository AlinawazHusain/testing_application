from pydantic import BaseModel


class add_new_hub_request(BaseModel):
    hub_name : str
    hub_lat : float 
    hub_lng : float 
    hub_pincode : str
    hub_address : str  
    

class add_new_hub_response(BaseModel):
    hub_address_book_uuid : str
    hub_name : str
    hub_pincode : str
    hub_full_address : str
    hub_google_location : str
    
    
class add_vehicle_to_hub_request(BaseModel):
    hub_address_book_uuid : str
    vehicle_uuid : str

class add_vehicle_to_hub_response(BaseModel):
    hub_address_book_uuid : str
    vehicle_uuid : str


class vehicle_hubs(BaseModel):
    hub_address_book_uuid : str
    hub_name : str|None
    hub_pincode : str
    hub_full_address : str
    hub_google_location : str
    vehicles_on_hub:float
    lat :float
    lng:float
    
class get_all_hubs_response(BaseModel):
    all_hubs : list[vehicle_hubs]
    
    
class remove_vehicle_from_hub_request(BaseModel):
    hub_address_book_uuid : str
    vehicle_uuid:str
    
class remove_vehicle_from_hub_response(BaseModel):
    removed_status :bool
    
class get_all_vehicles_on_hub_request(BaseModel):
    hub_address_book_uuid : str
    

class get_all_vehicles_on_hub_response(BaseModel):
    pass