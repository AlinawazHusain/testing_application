from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from auth.jwt import verify_token
from config.exceptions import ForbiddenError


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def role_required(required_role: str):
    """
    Dependency function for enforcing role-based access control in FastAPI routes.

    This function returns an asynchronous dependency that verifies:
    - The validity of the JWT token.
    - The user's role matches the required role.
    - The token provided is an access token.

    Args:
        required_role (str): The user role required to access the route (e.g., "mfo", "driver").

    Returns:
        Callable: An async dependency function for use with FastAPI's `Depends`.

    Raises:
        ForbiddenError: If the user's role does not match the required role or
                        if the token is not an access token.

    Example:
        @app.get("/admin/dashboard")
        async def dashboard(uuid: str = Depends(role_required("admin"))):
            return {"message": f"Hello admin with UUID {uuid}"}
    """
    
    async def role_checker(token: str = Depends(oauth2_scheme)):
        payload = await verify_token(token)
        role = payload['role']
        if role != required_role:
            raise ForbiddenError("You do not have permission to access this resource")
        
        if not payload['access_token']:
            raise ForbiddenError("Your token is not access token , Use an access token")
        return payload["uuid"]
    return role_checker



def driver_role_required():
    """
    Dependency function for enforcing role-based access control in FastAPI routes.

    This function returns an asynchronous dependency that verifies:
    - The validity of the JWT token.
    - The user's role matches the required role.
    - The token provided is an access token.


    Returns:
        Callable: An async dependency function for use with FastAPI's `Depends`.

    Raises:
        ForbiddenError: If the user's role does not match the required role or
                        if the token is not an access token.

    Example:
        @app.get("/driver/dashboard")
        async def dashboard(driver_uuid: str = Depends(driver_role_required())):
            return {"message": f"Hello driver with UUID {driver_uuid}"}
    """
    
    async def driver_role_checker(token: str = Depends(oauth2_scheme)):
        payload = await verify_token(token)
        role = payload['role']
        if role != "driver":
            raise ForbiddenError("You do not have permission to access this resource")
        
        if not payload['access_token']:
            raise ForbiddenError("Your token is not access token , Use an access token")
        return payload["driver_uuid"]
    return driver_role_checker



def mfo_role_required():
    """
    Dependency function for enforcing role-based access control in FastAPI routes.

    This function returns an asynchronous dependency that verifies:
    - The validity of the JWT token.
    - The user's role matches the required role.
    - The token provided is an access token.


    Returns:
        Callable: An async dependency function for use with FastAPI's `Depends`.

    Raises:
        ForbiddenError: If the user's role does not match the required role or
                        if the token is not an access token.

    Example:
        @app.get("/mfo/dashboard")
        async def dashboard(driver_uuid: str = Depends(mfo_role_required())):
            return {"message": f"Hello mfo with UUID {mfo_uuid}"}
    """
    
    async def mfo_role_checker(token: str = Depends(oauth2_scheme)):
        payload = await verify_token(token)
        role = payload['role']
        if role != "mfo":
            raise ForbiddenError("You do not have permission to access this resource")
        
        if not payload['access_token']:
            raise ForbiddenError("Your token is not access token , Use an access token")
        return payload["mfo_uuid"]
    return mfo_role_checker