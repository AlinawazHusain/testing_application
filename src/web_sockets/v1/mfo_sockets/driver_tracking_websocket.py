import asyncio
import json
from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy import desc
from auth.jwt import verify_token
from config.exceptions import ForbiddenError, UnauthorizedError
from db.database_operations import get_tuple_instance
from db.db import get_async_session_factory
from helpers.mfo_helpers.mfo_driver_helper import get_driver_status_and_current_activity
from integrations.location_service import get_location_name
from models.driver_models import DriverLocation
from utils.driver_activity_rule_engine import get_driver_activity
from utils.time_utils import convert_utc_to_ist, get_utc_time




driver_tracking_websocket_router = APIRouter()

connected_clients = []

@driver_tracking_websocket_router.websocket("/driverTrackingWS")
async def handler(websocket:WebSocket , session_factory = Depends(get_async_session_factory)):
    token = websocket.headers.get("Bearer")
    if not token:
        raise UnauthorizedError()
    
    payload = await verify_token(token)

    if not payload:
        raise ForbiddenError("Invalid token")
    
    await websocket.accept()
    connected_clients.append(websocket)
    driver_uuid = None
    mfo_uuid = payload["mfo_uuid"]
    try:
        message = None
        try:
            message = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        except asyncio.TimeoutError:
            await websocket.send_json({"error": "No driver_uuid received in time. Closing connection."})
            return

        data = json.loads(message)
        driver_uuid = data.get("driver_uuid")
        if not driver_uuid:
            await websocket.send_json({"error": "Missing driver_uuid in message"})
            return
        response = None
        while True:
            if driver_uuid:
                driver_location_updated_at = get_utc_time()
                
                async with session_factory() as db:
                        driver_location_instance = await get_tuple_instance(db , 
                                                    DriverLocation , 
                                                    {"driver_uuid" : driver_uuid} ,
                                                    order_by = [desc(DriverLocation.id)],
                                                    limit = 1
                                                    )
                        if driver_location_instance:
                            driver_location_updated_at = convert_utc_to_ist(driver_location_instance.created_at)
                            driver_status = await get_driver_activity(db , driver_uuid , mfo_uuid)
                            # await get_driver_status_and_current_activity(db , driver_uuid)
                            response = {
                                "driver_lat" : driver_location_instance.lat,
                                "driver_lng" : driver_location_instance.lng,
                                "driver_location" : await get_location_name(driver_location_instance.lat, driver_location_instance.lng),
                                "driver_location_updated_at" : driver_location_updated_at.isoformat(),
                                "driver_current_activity" : driver_status[1]
                            }
                        else:
                            response = None
                
                if response:
                    await websocket.send_json(response)
                    
                await asyncio.sleep(3)
    except Exception as e:
        print("WebSocket error:", e)
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        await websocket.close()