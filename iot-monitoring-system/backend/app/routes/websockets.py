from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json

router = APIRouter()

active_connections: Dict[str, WebSocket] = {}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    device_id = None

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if "deviceId" in message and "action" in message:
                device_id = message["deviceId"]
                action = message["action"]

                # Логика включения/выключения (например, через MQTT)
                device_status = action == "on"
                print(f"Устройство {device_id} -> {'Включено' if device_status else 'Выключено'}")

                # Отправляем обратно клиенту новый статус
                await websocket.send_text(json.dumps({"deviceId": device_id, "status": device_status}))

    except WebSocketDisconnect:
        print("Клиент отключился")
        if device_id and device_id in active_connections:
            del active_connections[device_id]
