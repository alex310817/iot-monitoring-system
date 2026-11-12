from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.routes import device_routes, user_routes, sensor_routes
from app.mqtt import client as mqtt_client
from app.routes import auth_routes  # Импортируем новый роутер
from fastapi.staticfiles import StaticFiles
import json
import logging
from app.routes import achievement_routes  # Add this line
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from slowapi.errors import RateLimitExceeded  # Add this import
from typing import List
from app.schemas import DeviceResponse
from app.database import get_db, AsyncSession
from app.models import User, Device
from app.routes.auth_routes import get_current_user  # Add this import
from sqlalchemy.future import select  # Add this import
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    debug=True,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"persistAuthorization": True},
    # Отключаем автоматическое перенаправление слешей
    redirect_slashes=False
)

# Add error middleware
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(e)}
        )

# Add trusted hosts
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1"]
)

# Optimize CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400  # Кэшируем CORS проверки на 24 часа
)

# Add Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Инструментатор для Prometheus
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)  # /metrics для Prometheus

# Подключение маршрутов API
app.include_router(auth_routes.router)
app.include_router(
    device_routes.router, 
    prefix="/devices",  # Add prefix here
    tags=["Devices"]
)
app.include_router(user_routes.router, prefix="/users", tags=["Users"])
app.include_router(sensor_routes.router, prefix="/sensors", tags=["Sensors"])
app.include_router(achievement_routes.router)  # Prefix is already included in router definition

# Add this after creating the FastAPI app
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# WebSocket соединения
active_connections = {}

@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: int):
    """Enhanced WebSocket endpoint with better error handling"""
    try:
        await websocket.accept()
        active_connections[device_id] = websocket
        logging.info(f"✅ WebSocket connected: device_id={device_id}")

        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if "action" in message:
                    topic = f"iot/home/{device_id}/control"
                    payload = json.dumps({"action": message["action"]})
                    mqtt_client.publish(topic, payload)
                    logging.info(f"📡 MQTT -> {topic}: {payload}")

                    await websocket.send_text(json.dumps({
                        "status": "success",
                        "device_id": device_id,
                        "action": message["action"]
                    }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": "Invalid JSON format"
                }))

    except WebSocketDisconnect:
        logging.info(f"❌ WebSocket disconnected: device_id={device_id}")
        active_connections.pop(device_id, None)
    except Exception as e:
        logging.error(f"⚠️ WebSocket error: {e}")
        if device_id in active_connections:
            active_connections.pop(device_id)

# 🔹 **Новый WebSocket API для iPhone**
@app.websocket("/ws/iphone")
async def websocket_iphone(websocket: WebSocket):
    """WebSocket API для iPhone"""
    await websocket.accept()
    print("✅ WebSocket подключен: iPhone")

    try:
        while True:
            data = await websocket.receive_text()
            command = json.loads(data)

            if "action" in command:
                action = command["action"]

                # Отправляем команду через MQTT
                mqtt_client.publish("iot/iphone/commands", json.dumps({"action": action}))
                print(f"📡 Отправлена команда на iPhone: {action}")

                # Отправляем подтверждение клиенту
                await websocket.send_text(json.dumps({"status": "sent", "action": action}))

    except WebSocketDisconnect:
        print("❌ WebSocket отключен: iPhone")

    except Exception as e:
        print(f"⚠️ Ошибка WebSocket iPhone: {e}")

# Управление жизненным циклом приложения
REDIS_CONFIG = {
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "retry_on_timeout": True,
    "max_connections": 10
}

@app.on_event("startup")
async def startup_event():
    """Initialize Redis and MQTT with optimized settings"""
    try:
        logger.info("Starting application services...")
        # Initialize Redis cache
        redis = aioredis.from_url(
            "redis://localhost",
            encoding="utf8",
            decode_responses=True,
            **REDIS_CONFIG
        )
        FastAPICache.init(
            RedisBackend(redis), 
            prefix="fastapi-cache",
            expire=300  # Default cache expiry of 5 minutes
        )
        
        # Start MQTT client
        mqtt_client.loop_start()
        logger.info("🚀 Services initialized successfully")
    except Exception as e:
        logger.error(f"⚠️ Service initialization error: {str(e)}", exc_info=True)
        # Continue even if Redis isn't available
        mqtt_client.loop_start()
        logger.warning("🚀 MQTT client started (Redis unavailable)")

@app.on_event("shutdown")
async def shutdown_event():
    """Остановка MQTT-клиента перед завершением приложения"""
    mqtt_client.loop_stop()
    print("🛑 MQTT-клиент остановлен")

# Simple server settings
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="localhost",
        port=8000,
        reload=True,
        workers=1,  # Один воркер для разработки
        log_level="error",  # Уменьшаем логирование
    )
