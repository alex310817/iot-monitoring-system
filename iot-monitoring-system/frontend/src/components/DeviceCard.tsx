import { useEffect, useState } from "react";

type DeviceProps = {
  id: string;
  name: string;
  status: boolean; // true - включено, false - выключено
};

const DeviceCard: React.FC<DeviceProps> = ({ id, name, status }) => {
  const [deviceStatus, setDeviceStatus] = useState(status);
  const [socket, setSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Подключаем WebSocket
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => {
      console.log("WebSocket подключен");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.deviceId === id) {
        setDeviceStatus(data.status);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket отключен");
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [id]);

  // Функция для отправки команды на сервер
  const toggleDevice = () => {
    if (socket) {
      socket.send(JSON.stringify({ deviceId: id, action: deviceStatus ? "off" : "on" }));
    }
  };

  return (
    <div className="p-4 border rounded-lg shadow-lg bg-white dark:bg-gray-800">
      <h3 className="text-lg font-semibold">{name}</h3>
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Статус: {deviceStatus ? "Включено" : "Выключено"}
      </p>
      <button
        onClick={toggleDevice}
        className={`mt-2 px-4 py-2 rounded-lg text-white ${
          deviceStatus ? "bg-red-500 hover:bg-red-600" : "bg-green-500 hover:bg-green-600"
        }`}
      >
        {deviceStatus ? "Выключить" : "Включить"}
      </button>
    </div>
  );
};

export default DeviceCard;
