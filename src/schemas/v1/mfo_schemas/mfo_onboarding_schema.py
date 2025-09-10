from typing import Optional
from pydantic import BaseModel


class mfo_send_otp_request(BaseModel):
    country_code : str
    phone_number : str


class mfo_send_otp_response(BaseModel):
    request_id : str


class mfo_verify_otp_request(BaseModel):
    country_code:str
    phone_number:str
    otp: str
    request_id:str
    fcm_token :str
    device_id : str
    ip_address : str
    device_model : str
    device_language : Optional[str] = "English UK"
    device_brand :str

class mfo_verify_otp_response(BaseModel):
    mfo_uuid:str
    exists : bool
    access_token : str
    refresh_token : str
    token_type : str


class mfo_refresh_access_token_request(BaseModel):
    refresh_token:str



class mfo_refresh_access_token_response(BaseModel):
    access_token : str
    token_type :str
    