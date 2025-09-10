import requests
from settings.credential_settings import credential_setting
from config.exceptions import NotFoundError


async def get_vehicle_data(vehicle_number:str):
    
    """
    Fetch vehicle registration details using the Attestr RC API.

    This function sends a POST request to Attestr's vehicle RC check API with the 
    provided vehicle registration number and returns the vehicle details if found.

    Args:
        vehicle_number (str): The vehicle registration number (e.g., "MH12AB1234").

    Returns:
        dict: A dictionary containing the vehicle's registration details if the request is successful.

    Raises:
        NotFoundError: If the response cannot be parsed as JSON or the data is unavailable.
    
    Notes:
        - The function expects a valid API key configured under `settings.attrstr_rc_key`.
        - In case of non-200 status, the raw response text is returned.
    """
    

    url = f"https://api.attestr.com/api/v2/public/checkx/rc"
    
    headers = {
        'Authorization': f'Basic {credential_setting.attrstr_rc_key}', 
        'Content-Type': 'application/json'
    }
    data = {
        "reg": vehicle_number
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        try:
            return response.json() 
        except ValueError:
            raise NotFoundError(f"Error: Unable to parse response as JSON. Response text: {response.text}")
    else:
        return response.text
    
    