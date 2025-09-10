from fastapi import Request
from schemas.v1.standard_schema import  standard_error_response, standard_success_response
from utils.time_utils import get_utc_time
from typing import Any
from pydantic import BaseModel
from collections.abc import Mapping, Sequence


def round_floats(obj: Any, precision: int = 2) -> Any:
    """
    Recursively round float values in any data structure.

    Args:
        obj (Any): The object we want to be modify for all its flaot values round off to precision decimal points.
        precision (int): decimal points upto which want to round off the float values.

    Returns:
        Any: Modified object with all float values rounded upto precision decimal points.
    """
    
    if isinstance(obj, float):
        return round(obj, precision)
    elif isinstance(obj, BaseModel):
        return round_floats(obj.model_dump())
    elif isinstance(obj, Mapping):
        return {k: round_floats(v, precision) for k, v in obj.items()}
    elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        return [round_floats(item, precision) for item in obj]
    else:
        return obj
    

def replace_underscores_in_values(obj:Any) -> Any:
    if isinstance(obj, BaseModel):
        return replace_underscores_in_values(obj.dict())
    if isinstance(obj, dict):
        return {k: replace_underscores_in_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_underscores_in_values(item) for item in obj]
    elif isinstance(obj, str):
        return obj.replace('_', ' ')
    else:
        return obj

    

def build_meta(request: Request) -> dict:
    """
    Constructs metadata for API responses.

    This metadata includes a timestamp, API version, execution time, 
    request path, and HTTP method. It's typically included in every API 
    response to provide context and traceability.

    Args:
        request (Request): The FastAPI request object containing request details.
        execution_time (str): Time taken to execute the request, in milliseconds (default is "0ms").

    Returns:
        dict: A dictionary containing standardized metadata fields for the API response.
    """
    
    end_time = get_utc_time()
    execution_time = f"{int((end_time - request.state.start_time).total_seconds() * 1000)} ms"
    
    
    return {
        "timestamp": request.state.start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": "1.0.0",
        "execution_time": execution_time,
        "path": request.url.path,
        "method": request.method,
    }

    
    
    
    
    

def success_response(request: Request,data=None, message="Success" , round_data = True):
    
    """
    Builds a standardized success response for FastAPI endpoints.

    The response includes a status of 'success', an optional message, 
    returned data, and metadata such as timestamp and execution details.

    Args:
        request (Request): The FastAPI request object.
        data (Any, optional): The actual response data payload (default is None).
        message (str, optional): A message describing the response (default is "Success").
        execution_time (str, optional): Time taken to execute the request (default is "0ms").

    Returns:
        standard_success_response: A Pydantic-validated success response schema.
    """
    if round_data:
        data = round_floats(data)
    
    # data = replace_underscores_in_values(data)
    response_data = {
        "status": "success",
        "message": message,
        "data": data,
        "meta": build_meta(request)
    }
    return standard_success_response(**response_data)







def error_response(request: Request, message="Something went wrong"):
    
    """
    Builds a standardized error response for FastAPI endpoints.

    The response includes a status of 'error', an error message, 
    a null data field, and metadata such as timestamp and request details.

    Args:
        request (Request): The FastAPI request object.
        message (str, optional): A message describing the error (default is "Something went wrong").
        execution_time (str, optional): Time taken to execute the request (default is "0ms").

    Returns:
        standard_error_response: A Pydantic-validated error response schema.
    """
    
    response_data =  {
        "status": "error",
        "message": message,
        "data": None,
        "meta": build_meta(request)
    }
    return standard_error_response(**response_data)