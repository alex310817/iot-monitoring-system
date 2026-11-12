import React, { useState, useEffect } from "react";
import { connectWebSocket } from "../utils/websocket";
import axios from "axios";

const API_URL = "http://localhost:8000/devices";

type Device = {
  id: number;
  name: string;
  status: string;
  temperature: number;
};

const DeviceControl: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);

  useEffect(() => {
    // Загружаем устройства при старте
    axios.get(API_URL).then((response) => setDevices(response.data));

    // Подключаем WebSocket
    const socket = connectWebSocket((data: unknown) => {
      const deviceData = data as { device_id: number; temperature: number };
      setDevices((prevDevices) =>
        prevDevices.map((device) =>
          device.id === deviceData.device_id
            ? { ...device, temperature: deviceData.temperature }
            : device
        )
      );
      setDevices((prevDevices) =>
        prevDevices.map((device) =>
          device.id === (data as { device_id: number; temperature: number }).device_id
            ? { ...device, temperature: (data as { device_id: number; temperature: number }).temperature }
            : device
        )
      );
    });

    return () => socket.close(); // Закрываем сокет при выходе
  }, []);

  const toggleDevice = async (deviceId: number, status: "on" | "off") => {
    await axios.post(`${API_URL}/${deviceId}/${status}`);
  };

  return (
    <div>
      <h2>📡 Устройства</h2>
      {devices.map((device) => (
        <div key={device.id}>
          <p>📟 {device.name} | 🌡 {device.temperature}°C | {device.status}</p>
          <button onClick={() => toggleDevice(device.id, "on")}>Включить</button>
          <button onClick={() => toggleDevice(device.id, "off")}>Выключить</button>
        </div>
      ))}
    </div>
  );
};

export default DeviceControl;
