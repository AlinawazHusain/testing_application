from enum import Enum
from pydantic import BaseModel, field_validator
from typing import Any, Optional


    
class create_profile_request(BaseModel):
    name : str
    years_of_experience : Optional[float] = 0
    number_of_vehicles : Optional[int] = 0
    number_of_evs : Optional[int] = 0

    
class create_profile_response(BaseModel):
    name : str
    years_of_experience : float
    number_of_vehicles : int
    number_of_evs : int
    
    

class mfo_update_main_file_valid_attributes(str, Enum):
    PROFILE_IMAGE = "profile_image"
    AADHAR_CARD = "aadhar_card"
    PAN_CARD = "pan_card"
    AADHAR_CARD_BACK = "aadhar_card_back"



class mfo_update_main_file_response(BaseModel):
    file_path :str
    main_profile_completion_percentage : float



class mfo_update_business_file_valid_attributes(str, Enum):
    LOGO = "logo"
    BUSINESS_PAN_CARD = "business_pan_card"
    MSME_CERTIFICATE = "msme_certificate"
    GST_CERTIFICATE = "gst_certificate"
    UDYAM_CERTIFICATE = "udyam_registration"
    SHOP_AND_ESTABLISHMENT_ACT_LICENSE = "shop_and_establishment_act_license"
    PARTNERSHIP_DEED = "partnership_deed"
    CERTIFICATE_OF_INCORPORATION = "certificate_of_incorporation"



class mfo_update_business_file_response(BaseModel):
    file_path :str
    business_docs_completion_percentage : float
    
    
    
class mfo_update_leasing_file_valid_attributes(str, Enum):
    BANK_STATEMENT = "bank_statement"
    ITR = "itr"
    BALANCE_SHEET = "balance_sheet"
    PROOF_OF_INCOME_FROM_LOGISTIC_BUSINESS = "proof_of_income_from_logistic_business"


class mfo_update_leasing_file_response(BaseModel):
    file_path :str
    leasing_docs_completion_percentage : float
    







class mfo_update_main_attributes_request(BaseModel):
    updates: dict[str, Any]

    @field_validator("updates")
    @classmethod
    def validate_updates(cls, updates: dict[str, Any]) -> dict[str, Any]:
        allowed_attributes = {
            "years_of_experience": (int, float),
            "name": str,
            "phone_number": str,
            "pincode": str,
            "city" : str,
            "email": str,
            "also_a_driver" : bool,
            "business_name" : str
        }
        
        invalid_keys = set(updates.keys()) - allowed_attributes.keys()
        if invalid_keys:
            raise ValueError(f"Invalid attributes provided: {invalid_keys}")

        # Validate each attribute type and additional constraints
        for key, value in updates.items():
            expected_type = allowed_attributes[key]
            if not isinstance(value, expected_type):
                raise ValueError(f"Invalid type for '{key}'. Expected {expected_type}, got {type(value)}")

            # Additional validation for specific fields
            if key == "years_of_experience" and value < 0:
                raise ValueError("'years_of_experience' must be a positive number.")

        return updates




class mfo_update_main_attributes_response(BaseModel):
    updated_data:dict[str , Any]
    
    
    
    
    
    


class mfo_update_business_attributes_request(BaseModel):
    updates: dict[str, Any]

    @field_validator("updates")
    @classmethod
    def validate_updates(cls, updates: dict[str, Any]) -> dict[str, Any]:
        allowed_attributes = {
            "pincode": str,
            "city" : str,
            "gst_number" : str,
            "business_name" : str,
            "total_number_of_vehicles" : int,
            "total_number_of_evs" : int,
            "operating_address" : str
        }
        
        invalid_keys = set(updates.keys()) - allowed_attributes.keys()
        if invalid_keys:
            raise ValueError(f"Invalid attributes provided: {invalid_keys}")

        # Validate each attribute type and additional constraints
        for key, value in updates.items():
            expected_type = allowed_attributes[key]
            if not isinstance(value, expected_type):
                raise ValueError(f"Invalid type for '{key}'. Expected {expected_type}, got {type(value)}")


        return updates




class mfo_update_business_attributes_response(BaseModel):
    updated_data:dict[str , Any]
    
class delete_account(BaseModel):
    deleted:bool
    
    
    
    




class mfo_update_leasing_attributes_request(BaseModel):
    updates: dict[str, Any]

    @field_validator("updates")
    @classmethod
    def validate_updates(cls, updates: dict[str, Any]) -> dict[str, Any]:
        allowed_attributes = {

            # "name": str,
            # "phone_number": str,
            # "pincode": str,
            # "city" : str,
            # "email": str,
            # "also_a_driver" : bool,
            # "business_name" : str
        }
        
        invalid_keys = set(updates.keys()) - allowed_attributes.keys()
        if invalid_keys:
            raise ValueError(f"Invalid attributes provided: {invalid_keys}")

        # Validate each attribute type and additional constraints
        for key, value in updates.items():
            expected_type = allowed_attributes[key]
            if not isinstance(value, expected_type):
                raise ValueError(f"Invalid type for '{key}'. Expected {expected_type}, got {type(value)}")

            # Additional validation for specific fields
            if key == "years_of_experience" and value < 0:
                raise ValueError("'years_of_experience' must be a positive number.")

        return updates




class mfo_update_leasing_attributes_response(BaseModel):
    updated_data:dict[str , Any]