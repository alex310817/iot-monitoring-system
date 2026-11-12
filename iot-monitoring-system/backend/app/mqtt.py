import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import SensorData, Device, User
import os
from app.database import sync_session_maker

# Update MQTT broker settings
MQTT_BROKER = "localhost"  # Change to local broker
MQTT_PORT = 1883                    # Standard MQTT port
TOPIC = "iot/#"                     # Topic pattern to subscribe to
MQTT_KEEPALIVE = 60
MQTT_RECONNECT_DELAY = 5
MQTT_CLIENT_ID = f"iot_backend_{os.getpid()}"  # Уникальный ID для каждого процесса

# Remove the old engine creation
# sync_engine = create_engine(os.getenv("DATABASE_URL").replace("postgresql+asyncpg", "postgresql"))
# SessionLocal = sessionmaker(bind=sync_engine)

# Add connection state tracking
mqtt_connected = False

def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

# Improved connection handling
def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print("✅ Connected to MQTT broker!")
        client.subscribe(TOPIC)
    else:
        mqtt_connected = False
        error_messages = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        print(f"❌ Failed to connect to MQTT broker: {error_messages.get(rc, f'Unknown error {rc}')}")

def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    if rc != 0:
        print("❌ Unexpected MQTT disconnection. Will attempt to reconnect...")
    else:
        print("ℹ️ MQTT client disconnected normally")

def parse_message(msg):
    """Enhanced message parser for multiple formats"""
    try:
        payload = msg.payload
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')

        # Try JSON decode first
        try:
            data = json.loads(payload)
            return data
        except json.JSONDecodeError:
            # Handle non-JSON formats
            if payload in ['on', 'off']:
                return {"status": payload}
            try:
                # Try numeric value - convert to dict
                float_value = float(payload)
                return {"value": float_value}
            except ValueError:
                return {"message": payload}

    except Exception as e:
        logging.error(f"Parse error: {e}")
        return None

def handle_device_message(topic: str, data: dict):
    """Handle device-specific messages with sync DB operations"""
    try:
        if 'status' in data:
            device_parts = topic.split('/')
            if len(device_parts) >= 4:
                device_id = device_parts[3]
                with sync_session_maker() as session:
                    admin = session.query(User).filter(User.email == "admin@example.com").first()
                    if not admin:
                        logging.error("❌ Admin user not found!")
                        return

                    device = session.query(Device).filter(Device.name == device_id).first()
                    is_new_device = not device
                    
                    if is_new_device:
                        device = Device(
                            name=device_id,
                            description=f"Auto-registered device {device_id}",
                            status=(data['status'] == 'on'),
                            owner_id=admin.id
                        )
                        session.add(device)
                        logging.info(f"🆕 New device registered: {device_id}")
                    
                    old_status = device.status if not is_new_device else None
                    device.status = (data['status'] == 'on')
                    device.last_update = datetime.now()
                    session.commit()
                    
                    if old_status != device.status or is_new_device:
                        status_emoji = "🟢" if device.status else "🔴"
                        status_text = "ON" if device.status else "OFF"
                        logging.info(f"{status_emoji} Device {device_id}: {status_text}")
                    
    except Exception as e:
        logging.error(f"❌ Device error: {str(e)}")

def on_message(client, userdata, msg):
    """Message handler with sync execution"""
    try:
        # Игнорируем тестовые сообщения и данные лифта
        if msg.topic.startswith('iot/elevator/test'):
            return
            
        data = parse_message(msg)
        if not data or not isinstance(data, dict):  # Add type check
            return

        # Логируем только важные сообщения
        if msg.topic.startswith('iot/home/') or msg.topic.startswith('iot/sensor/'):
            logging.info(f"📩 Received MQTT message on {msg.topic}: {data}")

        if msg.topic.startswith('iot/home/'):
            handle_device_message(msg.topic, data)
        elif msg.topic.startswith('iot/sensor/'):
            if 'value' in data:
                with sync_session_maker() as session:
                    new_data = SensorData(
                        device_id=int(msg.topic.split('/')[-1]),  # Convert to int
                        temperature=float(data['value']),
                        timestamp=datetime.now()
                    )
                    session.add(new_data)
                    session.commit()

    except Exception as e:
        logging.error(f"Message processing error: {e}", exc_info=True)

# Initialize MQTT client with clean session
client = mqtt.Client(
    client_id=MQTT_CLIENT_ID,
    clean_session=True,
    protocol=mqtt.MQTTv311,
    transport="tcp"
)

# Configure client
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Set connection parameters
client.reconnect_delay_set(min_delay=1, max_delay=MQTT_RECONNECT_DELAY)
client.connect_async(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)

# Add error handling for connection
try:
    # Start the loop in background thread
    client.loop_start()
except Exception as e:
    print(f"⚠️ MQTT initialization error: {e}")
    # Don't fail completely, just log the error
    pass

