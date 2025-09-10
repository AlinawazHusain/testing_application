import aiohttp
from settings.credential_settings import credential_setting

    

async def get_gst_Address(gst_number:str):
    """
    Fetch the registered address of a business using a GST number via the AppyFlow GST API.

    This function sends an asynchronous POST request to the AppyFlow API with the provided 
    GST number and retrieves the primary address (`pradr.addr`) of the taxpayer.

    Args:
        gst_number (str): The 15-character GST number of the organization.

    Returns:
        str: The concatenated full address of the GST-registered organization if successful,
             or an error message if the API call fails.

    Raises:
        Exception: If the API call or response parsing fails due to connectivity issues, 
                   unexpected data format, or other errors.
    """
    
    try:
        api_url = "https://appyflow.in/api/verifyGST"
        params = {
            "key_secret": credential_setting.appyflow_gst_api_key,
            "gstNo": gst_number,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    address = data["taxpayerInfo"]["pradr"]["addr"]
                    final_address = ""
                    for i in address:
                        final_address += address[i] + " " if address[i] != "" else ""
                    return final_address
                else:
                    return "Error to fetch address from API"
    except Exception as e:
        raise e
        