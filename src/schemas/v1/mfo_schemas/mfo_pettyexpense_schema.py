from typing import Any, Optional
from pydantic import BaseModel


class individual_petty_expense(BaseModel):
    driver_uuid:str|None
    vehicle_uuid:str|None
    driver_name:str|None
    driver_profile_image:str|None
    vehicle_number:str|None
    pettycash:float

class get_drivers_with_pettycash_request(BaseModel):
    month:int
    year:int

class get_drivers_with_pettycash_response(BaseModel):
    petty_expenses_per_driver:list[individual_petty_expense]


class get_vehicle_with_pettycash_request(BaseModel):
    month:int
    year:int
    
class get_vehicles_with_pettycash_response(BaseModel):
    petty_expense_per_vehicle:list[individual_petty_expense]
    


class add_pettyexpense_request(BaseModel):
    vehicle_uuid :Optional[str] = None
    driver_uuid : Optional[str] = None
    expense_currency : Optional[str] = 'INR'
    expense : float
    expense_description : Optional[str] = "No description for this petty expense"
    expense_date : int
    expense_month : int
    expense_year : int


class add_pettyexpense_response(BaseModel):
    petty_expense_uuid:str
    vehicle_uuid:str|None
    driver_uuid : str|None
    expense_currency: str
    expense : float
    expense_description : str
    
    
    
class get_pettyexpense_request(BaseModel):
    expense_month : int
    expense_year : int
    
class petty_expense(BaseModel):
    petty_expense_uuid:str
    vehicle_uuid:str|None
    driver_uuid:str|None
    expense_date:Any 
    expense_currency:str
    expense : float
    expense_description : str
    
    
class get_pettyexpense_response(BaseModel):
    petty_expenses : list[petty_expense]
    
    
    
    
    
    

class edit_pettyexpense_request(BaseModel):
    petty_expense_uuid : str
    expense:Optional[float] = None
    expense_description:Optional[str] = None
    
class edit_pettyexpense_response(BaseModel):
    edit_status : bool
    
    

class delete_pettyexpense_request(BaseModel):
    petty_expense_uuid : str
   
class delete_pettyexpense_response(BaseModel):
    delete_status : bool
    
    

class get_vehicle_pettyexpense_request(BaseModel):
    vehicle_uuid:str
    month:int
    year:int
    
class get_vehicle_pettyexpense(BaseModel):
    petty_expense_uuid:str
    vehicle_number:str
    pettycash:float
    expense_description : str
    expense_date:Any
    
class get_vehicle_pettyexpense_response(BaseModel):
    vehicle_pettyexpense:list[get_vehicle_pettyexpense]
    
    

class get_driver_pettyexpense_request(BaseModel):
    driver_uuid:str
    month:int
    year:int

    
class get_driver_pettyexpense(BaseModel):
    petty_expense_uuid:str
    driver_name:str
    driver_profile_image:str|None
    pettycash:float
    expense_description : str
    expense_date:Any
    
    
class get_driver_pettyexpense_response(BaseModel):
    driver_pettyexpense:list[get_driver_pettyexpense]