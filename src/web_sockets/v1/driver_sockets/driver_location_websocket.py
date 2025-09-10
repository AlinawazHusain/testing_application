from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from auth.jwt import verify_token
import json
from sqlalchemy.ext.asyncio import AsyncEngine
from config.exceptions import ForbiddenError, UnauthorizedError
from config.firebase_config import send_fcm_notification
from models.driver_models import DriverLocation, DriverMain
from db.db import get_async_db
from db.database_operations import update_table
from utils.time_utils import get_utc_time
from geoalchemy2.shape import from_shape
from shapely.geometry import Point



driver_location_websocket_router = APIRouter()

connected_clients = []

@driver_location_websocket_router.websocket("/LocationWS")
async def LocationWS(websocket: WebSocket , session:AsyncEngine = Depends(get_async_db)):
    
    """
    WebSocket endpoint for real-time driver location updates.

    This endpoint authenticates the user using a JWT token provided in the `Bearer` header.
    Once connected, it continuously listens for location data sent by the driver and 
    stores it in the `DriverLocation` table in the database.

    Key Features:
    - JWT-based authentication for secure communication.
    - Real-time ingestion of location data using a WebSocket stream.
    - On client disconnect, updates the `last_login` field of the driver in `DriverMain`.
    - Maintains a list of connected clients for potential future use (e.g., broadcasting).

    Args:
        websocket (WebSocket): The WebSocket connection instance.
        session (AsyncEngine): SQLAlchemy asynchronous session, injected via dependency.

    Raises:
        HTTPException: If the `Bearer` token is missing or invalid.
        WebSocketDisconnect: Handled gracefully by updating last_login and cleaning up.
    """
    

    token = websocket.headers.get("Bearer")
    if not token:
        raise UnauthorizedError()
    
    payload = await verify_token(token)

    if not payload:
        raise ForbiddenError("Invalid token")

    await websocket.accept()

    connected_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            if data["lat"] != 0 and data["lng"] != 0:
                data["location"]=from_shape(Point(data["lng"], data["lat"]))
                data_dict = DriverLocation(**data)
                data_dict.driver_uuid = payload['driver_uuid']
                session.add(data_dict)
                await session.commit()
    except WebSocketDisconnect:
        await update_table(session ,DriverMain, {"driver_uuid" : payload["driver_uuid"]} , {"last_login" :get_utc_time()})
        await session.commit()
        await session.close()
        connected_clients.remove(websocket)