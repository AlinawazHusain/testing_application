from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import json

from config.info_logger import logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log incoming API requests. This middleware logs details such as the HTTP method, 
    request URL, client IP address, user agent, and request body (if available). 

    If the request contains a file upload (multipart/form-data), the body is not logged as binary data,
    but a message indicating a file upload is logged instead. If the body is a valid JSON, it is parsed 
    and logged; otherwise, an error message is logged indicating the failure to parse the body.

    **Logging Information Includes:**
    - HTTP Method (e.g., GET, POST, etc.)
    - Request URL
    - Client IP address
    - User-Agent header
    - Request Body (or indication of file upload)

    This middleware provides useful insight into API requests for debugging, monitoring, and tracking purposes.

    Attributes:
        logger (logging.Logger): The logger instance used for logging the request information.
    
    Methods:
        dispatch(request: Request, call_next): 
            Processes the incoming request, logs the relevant information, and passes the request to the next middleware or handler.
    """

    async def dispatch(self, request: Request, call_next):
        
        """
        Intercepts the incoming request, logs relevant information, and passes the request to the next handler.

        Args:
            request (Request): The incoming request object.
            call_next (Callable): The function to call for processing the request after logging.

        Returns:
            Response: The response returned by the next middleware or the final handler.
        """
        
        client_ip = request.client.host if request.client else "Unknown IP"

        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            body_data = "File upload (binary data not logged)"
        else:
            body = await request.body()
            try:
                body_data = json.loads(body.decode("utf-8")) if body else None
            except json.JSONDecodeError:
                body_data = "Unable to parse body"

        logger.info(
            "API REQUEST",
            extra={
                "info": {
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("User-Agent", "Unknown"),
                    "body": body_data,
                }
            }
        )

        response = await call_next(request)
        return response
