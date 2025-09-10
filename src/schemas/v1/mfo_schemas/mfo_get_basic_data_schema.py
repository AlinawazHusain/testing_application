from pydantic import BaseModel


    
class get_profile_data_response(BaseModel):
    profile_image : str | None
    name : str | None
    phone_number : str
    pincode: str|None
    city : str|None
    alternative_phone_number : str | None
    pan_card : str | None
    aadhar_card : str | None
    aadhar_card_back :str | None
    verification_status : bool
    
    
class get_business_data_response(BaseModel):
    logo : str | None
    business_name : str | None
    gst_number : str | None
    operating_address : str | None
    pincode : str | None
    city : str | None
    total_number_of_vehicles : int | None
    total_number_of_evs : int | None
    business_docs_completion_percentage : float | None
    leasing_docs_completion_percentage : float | None
    
    

class get_business_docs_response(BaseModel):
    gst_certificate : str | None
    business_pan_card : str | None
    certificate_of_incorporation:str | None
    shop_and_establishment_act_license : str  | None
    udyam_registration : str | None
    partnership_deed : str | None
    msme_certificate : str | None
    

class get_leasing_docs_response(BaseModel):
    bank_statement : str | None
    itr : str | None
    balance_sheet : str | None
    proof_of_income_from_logistic_business :str | None