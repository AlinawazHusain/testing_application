import sys
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi import status
import traceback
import json

from utils.response import build_meta, error_response
from .error_logger import logger

# ✅ Define Custom Exceptions with HTTP Status Codes
class DatabaseError(HTTPException):
    def __init__(self, message="Database error occurred"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

class ServiceUnavailableError(HTTPException):
    def __init__(self, message="External service is unavailable"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=message)

class InvalidRequestError(HTTPException):
    def __init__(self, message="Invalid request parameters"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

class UnauthorizedError(HTTPException):
    def __init__(self, message="Unauthorized access"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

class UnprocessableEntityError(HTTPException):
    def __init__(self, message="Unprocessabel Entity"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)

class ForbiddenError(HTTPException):
    def __init__(self, message="Action forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)

class NotFoundError(HTTPException):
    def __init__(self, message="Requested resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)

class ConflictError(HTTPException):
    def __init__(self, message="Conflict detected in request"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=message)

class RateLimitError(HTTPException):
    def __init__(self, message="Too many requests, please try again later"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)

class TimeoutError(HTTPException):
    def __init__(self, message="Request timed out"):
        super().__init__(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=message)

class BadGatewayError(HTTPException):
    def __init__(self, message="Bad gateway error occurred"):
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=message)

class InternalServerError(HTTPException):
    def __init__(self, message="An internal server error occurred"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)


class NoCredentialsError(HTTPException):
    def __init__(self , message = "No credentials found."):
        super().__init__(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR , detail = message)
        

class PartialCredentialsError(HTTPException):
    def __init__(self , message = "Incomplete credentials provided"):
        super().__init__(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR , detail = message)
    

async def global_exception_handler(request: Request, exc: Exception):
    """Handles all uncaught exceptions globally and logs them in a structured format."""

    # Extract request details
    # request_id = request.headers.get("X-Request-ID", f"req-{request.scope.get('client', ('', ''))[1]}")
    # timestamp = request.headers.get("date", request.scope.get("time", "N/A"))

    # # ✅ Get Client IP (Handle Proxies)
    # client_ip = request.client.host if request.client else "Unknown"
    # forwarded_for = request.headers.get("X-Forwarded-For")
    # if forwarded_for:
    #     client_ip = forwarded_for.split(",")[0].strip() 

    # # ✅ User-Agent
    # user_agent = request.headers.get("User-Agent", "Unknown")

    # ✅ Attempt to Read Request Body (Handle Safely)
    # body = None
    # try:
    #     body_bytes = await request.body()
    #     body_str = body_bytes.decode("utf-8") if body_bytes else None
    #     body = json.loads(body_str) if body_str else None
    # except Exception:
    #     body = "[Could not retrieve body]"

    # ✅ Get Exception File & Line Number
    # file_name = None
    # line_number = None
    # if isinstance(exc, HTTPException):
    #     tb = traceback.extract_tb(sys.exc_info()[2])
    # else:
    #     tb = traceback.extract_tb(exc.__traceback__)

    # if tb:
    #     file_name, line_number, _, _ = tb[-1]
    
    # ✅ Build structured error log
    # error_log = {
    #     "timestamp": timestamp if timestamp != "N/A" else request.scope.get("time", "2025-03-21 00:00:00"),
    #     "level": "ERROR",
    #     "error_type": type(exc).__name__,
    #     "message": str(exc.detail) if isinstance(exc, HTTPException) else "Internal Server Error",
    #     "file": file_name,
    #     "line": line_number,
    #     "request": {
    #         "method": request.method,
    #         "url": str(request.url),
    #         "request_id": request_id,
    #         "client_ip": client_ip,
    #         "user_agent": user_agent,
    #         "body": body
    #     },
    #     "status_code": exc.status_code if isinstance(exc, HTTPException) else status.HTTP_500_INTERNAL_SERVER_ERROR
    # }

    # if not isinstance(exc, HTTPException):
    #     error_log["traceback"] = traceback.format_exc().replace("\n", " ")

    # # ✅ Log the structured error
    # logger.error("Error occurred:", extra={"error": error_log})

    
    status_code = exc.status_code if isinstance(exc, HTTPException) else status.HTTP_500_INTERNAL_SERVER_ERROR
    message = str(exc.detail) if isinstance(exc, HTTPException) else "Internal Server Error"
    
    response_data = {
        "status": "error",
        "message": message,
        "data": None,
        "meta": build_meta(request)
    }

    return JSONResponse(content=response_data, status_code=status_code)
    
