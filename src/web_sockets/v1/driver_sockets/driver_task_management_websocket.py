from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from typing import Dict
from auth.jwt import verify_token
from schemas.v1.driver_websockets_schemas.task_websocket_schema import TaskWSSchema
from settings.static_data_settings import static_table_settings
from utils.response import success_response




driver_task_management_websocket_router = APIRouter()


connected_clients: Dict[str, WebSocket] = {}


@driver_task_management_websocket_router.websocket("/TaskWS")
async def TaskWS(websocket: WebSocket):
    token = websocket.headers.get("Bearer")
    if not token:
        await websocket.close(code=4401)
        return

    payload = await verify_token(token)
    if not payload:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    driver_uuid = payload['driver_uuid']
    connected_clients[driver_uuid] = websocket

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.pop(driver_uuid, None)
        print(f"User {driver_uuid} disconnected.")



async def push_to_driver_task_page(request :Request , user_id: str , event:str ):
    websocket = connected_clients.get(user_id)
    if websocket:
        TASK_TYPES = static_table_settings.static_table_data["TASK_TYPES"]
        update = TaskWSSchema(event = event , points_earned = TASK_TYPES.get(event , 0))
        message = success_response(request , update , "task websocket data")
        await websocket.send_json(message.model_dump())
        return True
    return False


