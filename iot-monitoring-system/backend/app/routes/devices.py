from fastapi import APIRouter, HTTPException
import paho.mqtt.publish as publish

router = APIRouter()

@router.post("/devices/{device_id}/on")
async def turn_on_device(device_id: int):
    publish.single("iot/device", payload=f'{{"device_id": {device_id}, "status": "on"}}', hostname="localhost")
    return {"message": "Device turned on"}

@router.post("/devices/{device_id}/off")
async def turn_off_device(device_id: int):
    publish.single("iot/device", payload=f'{{"device_id": {device_id}, "status": "off"}}', hostname="localhost")
    return {"message": "Device turned off"}
# Compare this snippet from iot-monitoring-system/backend/app/schemas.py: