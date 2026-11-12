from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db, async_engine  # Добавляем импорт async_engine
from app.models import Device, User  # Add User to imports
from app.schemas import DeviceCreate, DeviceControl, DeviceResponse
from app.mqtt import client as mqtt_client
from app.routes.auth_routes import get_current_user
from app.routes.achievement_routes import check_achievements
from typing import List  # Add this import
import json
from fastapi_cache.decorator import cache
import serial.tools.list_ports
import asyncio
import logging

router = APIRouter()  # Changed from router = APIRouter(tags=["Devices"])

@router.post("/", status_code=status.HTTP_201_CREATED)  # Changed from "/devices"
async def create_device(
    device: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        new_device = Device(
            name=device.name,
            description=device.description,
            status=False,  # Always start with status False
            owner_id=current_user.id  # Set owner_id from current_user
        )
        db.add(new_device)
        await db.commit()
        
        # Check achievements immediately after adding device
        unlocked = await check_achievements(current_user.id, "devices_added", db)
        
        await db.refresh(new_device)
        
        return {
            "device": new_device,
            "unlocked_achievements": [
                {
                    "name": ach.name,
                    "description": ach.description,
                    "icon": ach.icon
                } for ach in unlocked
            ]
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DeviceResponse])
@cache(expire=30)
async def get_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's devices with authentication"""
    try:
        result = await db.execute(
            select(Device).where(Device.owner_id == current_user.id)
        )
        devices = result.scalars().all()
        return devices or []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{device_id}")
async def get_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Получает информацию об одном устройстве"""
    result = await db.execute(select(Device).filter(Device.id == device_id))
    device = result.scalars().first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return device

@router.post("/{device_id}/on")
async def turn_on_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Включает устройство"""
    result = await db.execute(select(Device).filter(Device.id == device_id))
    device = result.scalars().first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Отправляем команду через MQTT
    topic = f"devices/{device_id}/control"
    mqtt_client.publish(topic, json.dumps({"action": "on"}))
    print(f"📡 MQTT -> {topic}: on")

    # Обновляем статус устройства
    device.status = True
    await db.commit()
    await db.refresh(device)

    return {"device_id": device_id, "status": device.status}

@router.post("/{device_id}/off")
async def turn_off_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Выключает устройство"""
    result = await db.execute(select(Device).filter(Device.id == device_id))
    device = result.scalars().first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Отправляем команду через MQTT
    topic = f"devices/{device_id}/control"
    mqtt_client.publish(topic, json.dumps({"action": "off"}))
    print(f"📡 MQTT -> {topic}: off")

    # Обновляем статус устройства
    device.status = False
    await db.commit()
    await db.refresh(device)

    return {"device_id": device_id, "status": device.status}

@router.delete("/{device_id}")
async def delete_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Удаляет устройство из базы"""
    result = await db.execute(select(Device).filter(Device.id == device_id))
    device = result.scalars().first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    await db.delete(device)
    await db.commit()

    return {"message": "Device deleted successfully"}

@router.post("/{device_id}/control")
async def control_device(
    device_id: int,
    action: DeviceControl,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Control device state with authentication"""
    try:
        # Check device ownership
        result = await db.execute(
            select(Device).where(
                Device.id == device_id,
                Device.owner_id == current_user.id
            )
        )
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found or access denied"
            )

        # Изменяем MQTT топик на соответствующий формат
        topic = f"arduino/{device_id}"  # Упрощенный формат топика
        payload = action.action  # Отправляем просто "on" или "off"
        mqtt_client.publish(topic, payload)
        print(f"📡 MQTT -> {topic}: {payload}")

        # Обновляем статус в базе данных
        device.status = (action.action == "on")
        await db.commit()

        return {
            "status": "success", 
            "message": f"Command {action.action} sent",
        }

    except Exception as e:
        logging.error(f"Control error: {e}")  # Добавляем логирование ошибок
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/scan")
async def scan_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сканирование подключенных устройств"""
    try:
        devices = []
        logging.info("🔍 Starting device scan...")
        
        # Сканируем порты для Arduino
        ports = serial.tools.list_ports.comports()
        for port in ports:
            port_description = str(port.description).lower()
            logging.info(f"Found port: {port.device} - {port.description}")
            
            if any(identifier in port_description.lower() for identifier in 
                ['arduino', 'usb serial', 'ft232', 'ch340', 'usb-serial']):
                # Создаем устройство в базе данных
                try:
                    device = Device(
                        name=f"Arduino ({port.device})",
                        description=f"Arduino device at {port.device}",
                        status=True,
                        owner_id=current_user.id
                    )
                    db.add(device)
                    await db.commit()
                    await db.refresh(device)
                    
                    devices.append({
                        'id': device.id,  # Используем ID из базы данных
                        'name': device.name,
                        'manufacturer': port.manufacturer or 'Arduino',
                        'type': 'arduino',
                        'status': device.status,
                        'port': port.device
                    })
                    logging.info(f"✅ Found Arduino device: {devices[-1]}")
                except Exception as e:
                    logging.error(f"Error adding device to database: {e}")
                    continue
        
        logging.info(f"✅ Successfully added {len(devices)} devices to database")
        return {
            "status": "success",
            "devices": devices
        }
        
    except Exception as e:
        logging.error(f"Scan error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при сканировании устройств: {str(e)}"
        )
