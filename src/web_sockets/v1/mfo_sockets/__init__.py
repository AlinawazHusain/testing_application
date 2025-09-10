from fastapi import APIRouter
from .vehicle_tracking_websocket import vehicle_tracking_websocket_router
from .driver_tracking_websocket import driver_tracking_websocket_router
mfo_websocket_v1_router = APIRouter(tags = ["MFO websocket v1 router"])



mfo_websocket_v1_router.include_router(vehicle_tracking_websocket_router)
mfo_websocket_v1_router.include_router(driver_tracking_websocket_router)
