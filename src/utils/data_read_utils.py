import aiohttp
from fastapi import UploadFile
import pandas as pd
from io import BytesIO
    


async def get_json_from_url(url):
    """
    Fetch JSON data from a given URL using an asynchronous HTTP GET request.

    Args:
        url (str): The target URL from which to retrieve JSON content.

    Returns:
        dict | list | None: The parsed JSON data from the response if successful,
                            None if the response status is not 200,
                            or a dictionary containing an error message in case of exception.

    Example:
        data = await get_json_from_url("https://example.com/data.json")
    """
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}

    


async def read_file(uploaded_file: UploadFile):
    """
    Reads a user-uploaded CSV or Excel file and returns it as a Pandas DataFrame.

    Supports:
    - CSV files (.csv)
    - Excel files (.xlsx)

    Args:
        uploaded_file (UploadFile): File uploaded via FastAPI's file upload interface.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the parsed data.
                      Returns an empty DataFrame if the file type is unsupported.

    Raises:
        ValueError: If reading the file content fails or file format is invalid.

    Example:
        df = await read_file(file)
    """

    content = uploaded_file.file.read()
    
    if uploaded_file.filename.endswith(".csv"):
        return pd.read_csv(BytesIO(content))
    elif uploaded_file.filename.endswith(".xlsx"):
        return pd.read_excel(BytesIO(content))
    
    return pd.DataFrame()
    

