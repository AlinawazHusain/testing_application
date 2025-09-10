from jose import ExpiredSignatureError, JWTError, jwt
from datetime import timedelta , datetime, timezone
from settings.credential_settings import credential_setting
from config.exceptions import UnauthorizedError , InternalServerError

ACCESS_TOKEN_EXPIRE_MINUTES = 720
REFRESH_TOKEN_EXPIRE_MINUTES = 0 




async def create_access_token(
    data: dict,
    expires_delta: timedelta = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES),
):
    """
    Create a JWT access token.

    Adds a flag `access_token: True` to the payload and generates a JWT token
    that expires after a specified duration.

    Args:
        data (dict): The payload data to encode in the JWT.
        expires_delta (timedelta, optional): The expiration duration of the token. 
                                             Defaults to 60 minutes.

    Returns:
        str: Encoded JWT token as a string.

    Raises:
        InternalServerError: If token generation fails due to internal error.
    """
    
    try:
        data['access_token'] = True
        to_encode = data.copy()
        expire = datetime.now(timezone.utc).replace(tzinfo=None) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, credential_setting.jwt_secret_key, algorithm = credential_setting.jwt_hashing_algorithm
        )
        return encoded_jwt
    
    except Exception as e:
        raise InternalServerError(message=f"Failed to create access token: {str(e)}")
    




async def create_refresh_token(
    data: dict,
    expires_delta: timedelta = timedelta(minutes = REFRESH_TOKEN_EXPIRE_MINUTES),
):
    
    """
    Create a JWT refresh token.

    Adds a flag `access_token: False` to the payload and generates a JWT token.
    This token typically has a longer or infinite expiry time.

    Args:
        data (dict): The payload data to encode in the JWT.
        expires_delta (timedelta, optional): Expiration duration of the token. 
                                             Defaults to 0 minutes (non-expiring).

    Returns:
        str: Encoded JWT token as a string.

    Raises:
        InternalServerError: If token generation fails due to internal error.
    """
    
    try:
        data['access_token'] = False
        to_encode = data.copy()
        expire = datetime.now(timezone.utc).replace(tzinfo=None) + expires_delta
        # to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, credential_setting.jwt_secret_key, algorithm = credential_setting.jwt_hashing_algorithm
        )
        return encoded_jwt
    
    except Exception as e:
        raise InternalServerError(message=f"Failed to create refresh token: {str(e)}")






async def verify_token(token: str):
    """
    Decode and verify a JWT token.

    Verifies the token's signature, expiration, and structure using the configured secret key and algorithm.

    Args:
        token (str): JWT token string to decode and validate.

    Returns:
        dict: The decoded payload from the token if verification is successful.

    Raises:
        UnauthorizedError: If the token is invalid or has expired.
        InternalServerError: For unexpected internal errors during verification.
    """
    
    try:
        payload = jwt.decode(token, credential_setting.jwt_secret_key, algorithms = [credential_setting.jwt_hashing_algorithm])
        return payload

    except ExpiredSignatureError:
        raise UnauthorizedError(message="Token has expired")

    except JWTError:
        raise UnauthorizedError(message="Invalid token")

    except Exception as e:
        raise InternalServerError(message="Unexpected error during token verification: {str(e)}")