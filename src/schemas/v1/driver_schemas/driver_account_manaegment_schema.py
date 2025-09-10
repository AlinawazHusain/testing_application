from enum import Enum
from pydantic import BaseModel, field_validator
from typing import Any



class driver_update_main_file_valid_attributes(str, Enum):
    PROFILE_IMAGE = "profile_image"
    AADHAR_CARD = "aadhar_card"
    PAN_CARD = "pan_card"
    DRIVING_LICENSE = "driving_license"
    AADHAR_CARD_BACK = "aadhar_card_back"



class driver_update_main_file_response(BaseModel):
    file_attribute: str
    file_path :str
    completion_percentage : float
    
    
    

class driver_update_main_attributes_request(BaseModel):
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
            "used_ev_before": bool,
            "alternative_phone_number": str,
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




class driver_update_main_attributes_response(BaseModel):
    updated_data:dict[str , Any]