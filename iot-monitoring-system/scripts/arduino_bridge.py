import serial
import serial.tools.list_ports
import paho.mqtt.client as mqtt
import json
import time
import logging
from threading import Thread

class ArduinoManager:
    def __init__(self):
        self.arduino = None
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.last_ping = 0
        self.device_id = None
        self.connected = False
        self.retries = 0
        self.max_retries = 3
        self.port_path = None
        self.connect_attempts = 0
        self.max_attempts = 3
        self.retry_delay = 2
        self.device_ready = False
        self.last_message_time = 0
        self.last_status = None
        
        # Подключаемся к MQTT брокеру
        try:
            self.mqtt_client.connect("localhost", 1883, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            logging.error(f"MQTT connection error: {e}")

    def on_connect(self, client, userdata, flags, rc):
        logging.info("Connected to MQTT broker")
        # Подписываемся на все команды управления
        client.subscribe("arduino/+/control")  # Изменён топик
        print("✅ Подписались на топик arduino/+/control")

    def on_message(self, client, userdata, msg):
        try:
            print(f"📥 Получено MQTT сообщение: {msg.topic} = {msg.payload.decode()}")
            # Получаем команду напрямую, без JSON
            command = msg.payload.decode().strip()
            if command in ['on', 'off']:
                print(f"🔄 Отправка команды на Arduino: {command}")
                self.send_command(command)
                
                # Добавляем подтверждение получения команды
                device_id = msg.topic.split('/')[1]
                self.mqtt_client.publish(f"arduino/{device_id}/status", command)
                
        except Exception as e:
            logging.error(f"Ошибка обработки сообщения: {e}")

    def find_arduino(self):
        """Поиск Arduino среди USB-устройств"""
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if "FT232R" in port.description or any(x in port.description.lower() for x in ['arduino', 'ch340']):
                    self.port_path = port.device
                    logging.info(f"✅ Arduino найдена на порту {port.device}")
                    return port.device
            return None
        except Exception as e:
            logging.error(f"❌ Ошибка поиска порта: {e}")
            return None

    def connect_arduino(self):
        """Подключение к Arduino с повторными попытками"""
        while self.connect_attempts < self.max_attempts:
            try:
                if not self.port_path:
                    self.port_path = self.find_arduino()
                
                if self.port_path:
                    self.arduino = serial.Serial(
                        port=self.port_path,
                        baudrate=9600,
                        timeout=1,
                        write_timeout=1
                    )
                    if self.arduino.is_open:
                        self.arduino.reset_input_buffer()
                        self.arduino.reset_output_buffer()
                        self.connect_attempts = 0  # Сброс счетчика после успешного подключения
                        logging.info("✅ Успешное подключение к Arduino")
                        return True
            except Exception as e:
                logging.error(f"❌ Ошибка подключения: {e}")
                self.connect_attempts += 1
                if self.arduino:
                    try:
                        self.arduino.close()
                    except:
                        pass
                self.arduino = None
                time.sleep(self.retry_delay)
        
        self.connect_attempts = 0  # Сброс счетчика после всех попыток
        return False

    def send_command(self, command):
        """Send command to Arduino"""
        if not self.arduino or not self.arduino.is_open:
            if not self.connect_arduino():
                return False

        try:
            # Clear buffers
            self.arduino.reset_input_buffer()
            self.arduino.reset_output_buffer()
            
            # Send command
            command_str = f"{command}\n"
            print(f"📤 Sending to Arduino: {command}")
            self.arduino.write(command_str.encode())
            self.arduino.flush()
            
            # Wait for response
            time.sleep(0.1)
            while self.arduino.in_waiting:
                response = self.arduino.readline().decode().strip()
                if response:
                    print(f"📥 Arduino response: {response}")
                    self.process_arduino_message(response)
            
            return True
        except Exception as e:
            print(f"❌ Send error: {str(e)}")
            self.reconnect()
            return False

    def read_arduino(self):
        """Чтение данных с Arduino"""
        while True:
            if self.arduino and self.arduino.is_open:
                try:
                    if self.arduino.in_waiting:
                        line = self.arduino.readline().decode().strip()
                        self.process_arduino_message(line)
                    
                    # Проверяем время последнего сообщения
                    if self.device_ready and time.time() - self.last_message_time > 3:
                        self.device_ready = False
                        self.reconnect()
                except Exception as e:
                    print(f"❌ Read error: {str(e)}")
                    self.reconnect()
            else:
                self.reconnect()
            time.sleep(0.1)

    def process_arduino_message(self, message):
        """Process messages from Arduino"""
        try:
            # Update last message time
            self.last_message_time = time.time()
            
            if not message.strip():
                return

            # Handle status messages
            if message.startswith("STATUS:"):
                status = message.split(":")[1].strip()
                self.last_status = status
                print(f"📊 Arduino Status: {status}")
                
                # Update connection state
                self.device_ready = True
                
                # Send status via MQTT if needed
                if self.device_id:
                    self.mqtt_client.publish(
                        f'arduino/{self.device_id}/status',
                        status.lower()  # Convert to lowercase for consistency
                    )
                return

            # Handle simple confirmations
            if message in ["ON", "OFF"]:
                print(f"✅ Command confirmed: {message}")
                return

            print(f"📝 Unknown message: {message}")

        except Exception as e:
            print(f"❌ Message processing error: {str(e)}")

    def reconnect(self):
        """Безопасное переподключение к Arduino"""
        print("🔄 Reconnecting to Arduino...")
        if self.arduino:
            try:
                self.arduino.close()
            except:
                pass
        self.arduino = None
        self.device_ready = False
        time.sleep(2)  # Увеличиваем задержку перед переподключением
        return self.connect_arduino()

    def run(self):
        """Основной цикл работы"""
        if self.connect_arduino():
            print("✅ Arduino подключена")
            # Запускаем поток для чтения данных
            read_thread = Thread(target=self.read_arduino)
            read_thread.daemon = True
            read_thread.start()
            
            # Мониторинг подключения
            while True:
                if time.time() - self.last_ping > 5:  # Если нет пинга больше 5 секунд
                    print("⚠️ Потеряна связь с Arduino")
                    self.reconnect()
                time.sleep(1)
        else:
            print("❌ Arduino не найдена")

if __name__ == "__main__":
    manager = ArduinoManager()
    manager.run()
