import httpx
from settings.credential_settings import credential_setting
from config.error_logger import logger
from config.exceptions import (
    ServiceUnavailableError,
    BadGatewayError,
    InternalServerError,
    UnprocessableEntityError,
)


async def send_otp(country_code: str, phone_number: str):
    """
    Sends an OTP (One-Time Password) to the specified phone number using the 2Factor API.

    Constructs the API request using the provided country code and phone number,
    and handles responses and errors accordingly.

    Args:
        country_code (str): The country code (e.g., '+91' for India).
        phone_number (str): The phone number to which the OTP should be sent.

    Returns:
        str: A request ID (Details from 2Factor API) to be used for OTP verification.

    Raises:
        ServiceUnavailableError: If the 2Factor API returns an error status.
        BadGatewayError: If the 2Factor service is unreachable.
        InternalServerError: For any unexpected exceptions.
    """
    try:
        # hash_key = quote(credential_setting.hash_key_otp) 
        f2_api_key = credential_setting.twofactor_avaronn_api_key
        template_name = "electrasphere" 

        url = f"https://2factor.in/API/V1/{f2_api_key}/SMS/{country_code + phone_number}/AUTOGEN/{template_name}"
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)

        data = response.json()

        if response.status_code != 200 or data.get("Status") != "Success":
            raise ServiceUnavailableError(f"Failed to send OTP: {data.get('Details')}")

        return data.get("Details")

    except httpx.RequestError as e:
        raise BadGatewayError("OTP Service Unreachable. Please try again later.")

    except ServiceUnavailableError as e:
        raise e
    
    except Exception as e:
        raise InternalServerError("Unexpected error occurred while sending OTP. Please try again.")



async def verify_otp(otp: str, request_id: str):
    
    """
    Verifies the OTP entered by the user against the 2Factor API.

    This function sends the OTP and request ID to the 2Factor verification endpoint
    and interprets the response to determine success or failure.

    Args:
        otp (str): The OTP entered by the user.
        request_id (str): The request ID returned by `send_otp`.

    Returns:
        dict: A dictionary containing a success message if the OTP is verified.

    Raises:
        UnprocessableEntityError: If the OTP is incorrect or invalid.
        BadGatewayError: If the verification service is unreachable or returns an invalid response.
        InternalServerError: For any unexpected errors during verification.
    """
    
    try:
        f2_api_key = credential_setting.twofactor_avaronn_api_key
        verify_url = f"https://2factor.in/API/V1/{f2_api_key}/SMS/VERIFY/{request_id}/{otp}"


        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(verify_url)

        try:
            verify_data = response.json()
        except Exception as json_error:
            raise BadGatewayError("Invalid response from OTP service. Please try again.")

        status_text = verify_data.get("Status", "Unknown")
        details = verify_data.get("Details", "No details provided")

        if response.status_code in [400, 401] or status_text != "Success":
            logger.warning(f"OTP verification failed - Request ID: {request_id}, Status: {status_text}, Details: {details}")
            raise UnprocessableEntityError("Invalid OTP provided.")

        return {"message": "OTP verified successfully"}

    except httpx.RequestError as e:
        raise BadGatewayError("OTP Verification Service Unreachable. Please try again later.")

    except UnprocessableEntityError as e:
        raise e 
    except BadGatewayError as e:
        raise e
    except Exception as e:
        raise InternalServerError("Unexpected error occurred while verifying OTP. Please try again.")
