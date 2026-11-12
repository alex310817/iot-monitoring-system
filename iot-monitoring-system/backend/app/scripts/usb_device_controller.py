import usb.core
import usb.util
import paho.mqtt.client as mqtt
import json
import logging

logging.basicConfig(level=logging.INFO)

class USBDeviceController:
    def __init__(self):
        self.devices = {}
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
    def find_mouse_devices(self):
        # Поиск всех USB-мышек
        devices = usb.core.find(find_all=True, bDeviceClass=0)
        mouse_devices = []
        
        for device in devices:
            try:
                if device.bDeviceClass == 0:  # HID устройства
                    for cfg in device:
                        for intf in cfg:
                            if intf.bInterfaceClass == 3:  # HID класс
                                if intf.bInterfaceSubClass == 1:  # Boot Interface
                                    if intf.bInterfaceProtocol == 2:  # Mouse
                                        mouse_devices.append({
                                            'id': f"{device.idVendor:04x}:{device.idProduct:04x}",
                                            'name': usb.util.get_string(device, device.iProduct),
                                            'manufacturer': usb.util.get_string(device, device.iManufacturer),
                                            'status': True
                                        })
                                        self.devices[device.idVendor] = device
            except:
                continue
                
        return mouse_devices

    def control_device(self, vendor_id, action):
        try:
            device = self.devices.get(int(vendor_id, 16))
            if not device:
                return False
                
            if action == 'off':
                usb.util.dispose_resources(device)
                device.reset()
            elif action == 'on':
                device.reset()
                
            return True
        except Exception as e:
            logging.error(f"Error controlling device: {e}")
            return False

    def on_connect(self, client, userdata, flags, rc):
        logging.info("Connected to MQTT broker")
        client.subscribe("usb/device/+/control")

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload)
            device_id = msg.topic.split('/')[2]
            action = data.get('action')
            
            if action in ['on', 'off']:
                success = self.control_device(device_id, action)
                logging.info(f"Device {device_id} {action}: {'success' if success else 'failed'}")
                
        except Exception as e:
            logging.error(f"Error processing message: {e}")

    def start(self):
        self.mqtt_client.connect("localhost", 1883, 60)
        self.mqtt_client.loop_forever()

if __name__ == "__main__":
    controller = USBDeviceController()
    controller.start()