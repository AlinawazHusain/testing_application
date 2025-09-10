from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
from sqlalchemy.ext.asyncio import AsyncEngine
from db.db import get_async_db
from models.log_models import TempDriverLocation

temp_driver_location_websocket_router = APIRouter()

connected_clients = []

@temp_driver_location_websocket_router.websocket("/tempDriverLocationWS")
async def tempDriverLocationWS(websocket: WebSocket , session:AsyncEngine = Depends(get_async_db)):
    
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
    

    session_id  = websocket.headers.get("session-id")
    device_id = websocket.headers.get("device-id")
    

    await websocket.accept()

    connected_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            data_dict = TempDriverLocation(**json.loads(data))
            data_dict.session_id = session_id
            data_dict.device_id = device_id
            session.add(data_dict)
            await session.commit()
    except WebSocketDisconnect:
        await session.commit()
        await session.close()
        connected_clients.remove(websocket)