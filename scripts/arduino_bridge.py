import serial
import serial.tools.list_ports
import paho.mqtt.client as mqtt
import json
import time
import logging
from threading import Thread
import subprocess
import platform

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ArduinoManager:
    def __init__(self):
        logging.info("🚀 Инициализация ArduinoManager...")
        self.arduino = None
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.last_ping = 0
        self.device_id = None
        self.port_name = None
        self.port_retry_count = 0
        self.max_retries = 3
        
        try:
            logging.info("📡 Подключение к MQTT брокеру...")
            self.mqtt_client.connect("localhost", 1883, 60)
            self.mqtt_client.loop_start()
            logging.info("✅ Подключено к MQTT брокеру")
        except Exception as e:
            logging.error(f"❌ Ошибка подключения к MQTT: {e}")

    def on_connect(self, client, userdata, flags, rc):
        logging.info("Connected to MQTT broker with result code: %s", rc)
        client.subscribe("iot/device/+/control")

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload)
            if self.device_id and msg.topic == f"iot/device/{self.device_id}/control":
                if data.get('action') in ['on', 'off']:
                    self.send_command(data['action'])
        except Exception as e:
            logging.error(f"Ошибка обработки сообщения: {e}")

    def find_arduino(self):
        """Поиск Arduino среди USB-устройств"""
        logging.info("🔍 Поиск Arduino...")
        ports = list(serial.tools.list_ports.comports())
        logging.info(f"Найдены порты: {[port.description for port in ports]}")
        
        for port in ports:
            logging.info(f"Проверка порта: {port.device} - {port.description}")
            # Расширяем список идентификаторов для Arduino
            if any(identifier in port.description.lower() for identifier in [
                'arduino',
                'usb-serial',
                'ft232r',  # FTDI chip
                'ch340',   # CH340 chip
                'cp210x'   # CP210x chip
            ]):
                logging.info(f"✅ Arduino найдена на порту {port.device}")
                return port.device
                
        logging.warning("❌ Arduino не найдена")
        return None

    def release_port(self, port_name):
        """Release the port if it's busy"""
        system = platform.system()
        if system == "Darwin":  # macOS
            try:
                # Check what's using the port
                lsof = subprocess.run(['lsof', port_name], capture_output=True, text=True)
                if lsof.stdout:
                    # Extract PID of process using the port
                    for line in lsof.stdout.split('\n')[1:]:  # Skip header
                        if line:
                            pid = line.split()[1]
                            logging.info(f"Attempting to terminate process {pid} using {port_name}")
                            subprocess.run(['kill', '-9', pid])
                            time.sleep(1)  # Wait for port to be released
                    return True
            except Exception as e:
                logging.error(f"Failed to release port: {e}")
        return False

    def connect_arduino(self):
        """Подключение к Arduino с освобождением порта"""
        arduino_port = self.find_arduino()
        if arduino_port:
            self.port_name = arduino_port
            
            # Try to connect multiple times
            for attempt in range(self.max_retries):
                try:
                    logging.info(f"Connection attempt {attempt + 1} of {self.max_retries}")
                    
                    # If port is busy, try to release it
                    try:
                        self.arduino = serial.Serial(arduino_port, 9600, timeout=1)
                        time.sleep(2)
                        logging.info("✅ Successfully connected to Arduino")
                        return True
                    except serial.SerialException as e:
                        if "busy" in str(e).lower():
                            logging.warning(f"Port {arduino_port} is busy, attempting to release...")
                            if self.release_port(arduino_port):
                                logging.info("Port released, retrying connection...")
                                time.sleep(2)  # Wait for port to be fully released
                                continue
                        raise e
                        
                except Exception as e:
                    logging.error(f"Connection attempt {attempt + 1} failed: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2)  # Wait before next attempt
                    else:
                        logging.error("❌ Failed to connect after maximum retries")
                        return False
                    
            return False
        return False

    def send_command(self, command):
        """Отправка команды на Arduino"""
        if self.arduino and self.arduino.is_open:
            try:
                self.arduino.write(f"{command}\n".encode())
                logging.info(f"📤 Отправлена команда: {command}")
            except Exception as e:
                logging.error(f"❌ Ошибка отправки команды: {e}")

    def read_arduino(self):
        """Чтение данных с Arduino"""
        while True:
            if self.arduino and self.arduino.is_open:
                try:
                    if self.arduino.in_waiting:
                        line = self.arduino.readline().decode().strip()
                        self.process_arduino_message(line)
                except Exception as e:
                    logging.error(f"❌ Ошибка чтения с Arduino: {e}")
                    self.reconnect()
            else:
                self.reconnect()
            time.sleep(0.1)

    def process_arduino_message(self, message):
        """Обработка сообщений от Arduino"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'connect':
                self.device_id = data.get('id')
                # Публикуем информацию о подключении устройства
                self.mqtt_client.publish('iot/devices/discovery', 
                                      json.dumps({
                                          'id': data.get('id'),
                                          'name': data.get('name'),
                                          'type': 'arduino',
                                          'status': 'connected'
                                      }))
                logging.info(f"✅ Arduino устройство {data.get('name')} подключено")
            
            elif msg_type == 'ping':
                self.last_ping = time.time()
            
            elif msg_type == 'status':
                if self.device_id:
                    self.mqtt_client.publish(f'iot/device/{self.device_id}/status', 
                                          json.dumps({'status': data.get('status')}))
                    logging.info(f"📊 Статус устройства: {data.get('status')}")
        
        except json.JSONDecodeError:
            logging.error(f"❌ Некорректный JSON от Arduino: {message}")

    def reconnect(self):
        """Переподключение к Arduino"""
        if self.arduino:
            try:
                self.arduino.close()
            except:
                pass
            self.arduino = None
            
        if self.device_id:
            # Публикуем информацию об отключении
            self.mqtt_client.publish('iot/devices/discovery', 
                                  json.dumps({
                                      'id': self.device_id,
                                      'status': 'disconnected'
                                  }))
            self.device_id = None
            
        time.sleep(1)
        self.connect_arduino()

    def run(self):
        """Основной цикл работы"""
        logging.info("🚀 Запуск ArduinoManager...")
        if self.connect_arduino():
            logging.info("✅ Arduino подключена и готова к работе")
            read_thread = Thread(target=self.read_arduino)
            read_thread.daemon = True
            read_thread.start()
            logging.info("✅ Поток чтения данных запущен")
            
            try:
                while True:
                    if time.time() - self.last_ping > 5:
                        logging.warning("⚠️ Потеряна связь с Arduino")
                        self.reconnect()
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.info("👋 Завершение работы...")
                if self.arduino:
                    self.arduino.close()
                self.mqtt_client.loop_stop()
        else:
            logging.error("❌ Не удалось подключиться к Arduino")

if __name__ == "__main__":
    try:
        manager = ArduinoManager()
        manager.run()
    except KeyboardInterrupt:
        logging.info("👋 Программа завершена пользователем")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")
