import React, { useEffect, useState } from "react";

interface Device {
    id: number;
    name: string;
    status: "online" | "offline";
}

interface DeviceListProps {
    token: string;
}

const DeviceList: React.FC<DeviceListProps> = ({ token }) => {
    const [devices, setDevices] = useState<Device[]>([]);
    const [newDeviceName, setNewDeviceName] = useState("");
    const [newDeviceStatus, setNewDeviceStatus] = useState<"online" | "offline">("offline");

    useEffect(() => {
        const fetchDevices = async () => {
            try {
                const response = await fetch("http://127.0.0.1:8000/devices", {
                    headers: { Authorization: `Bearer ${token}` },
                });

                if (!response.ok) {
                    throw new Error("Ошибка загрузки устройств");
                }

                const data = await response.json();
                setDevices(data.devices || []);
            } catch (error) {
                console.error(error);
                setDevices([]);
            }
        };

        fetchDevices();
    }, [token]);

    const addDevice = async () => {
        try {
            const data = {
                name: newDeviceName,
                status: newDeviceStatus, // Теперь передаём строку "online" или "offline"
                description: "",
            };

            const response = await fetch("http://127.0.0.1:8000/devices", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Ошибка добавления устройства: ${errorText}`);
            }

            const newDevice = await response.json();
            setDevices((prev) => [...prev, newDevice]);
            setNewDeviceName("");
        } catch (error) {
            console.error(error);
        }
    };

    const toggleDevice = async (deviceId: number, currentStatus: "online" | "offline") => {
        try {
            const newStatus = currentStatus === "online" ? "offline" : "online";

            await fetch(`http://127.0.0.1:8000/devices/${deviceId}`, {
                method: "PATCH", // Меняем метод на PATCH для обновления статуса
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ status: newStatus }),
            });

            setDevices((prev) =>
                prev.map((device) =>
                    device.id === deviceId ? { ...device, status: newStatus } : device
                )
            );
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <div>
            <h2>➕ Добавить устройство</h2>
            <input
                type="text"
                placeholder="Название устройства"
                value={newDeviceName}
                onChange={(e) => setNewDeviceName(e.target.value)}
            />
            <select value={newDeviceStatus} onChange={(e) => setNewDeviceStatus(e.target.value as "online" | "offline")}>
                <option value="online">Online</option>
                <option value="offline">Offline</option>
            </select>
            <button onClick={addDevice}>Добавить</button>

            <h2>📡 Устройства:</h2>
            <ul>
                {devices.map((device) => (
                    <li key={device.id}>
                        {device.name} - {device.status === "online" ? "🟢 Online" : "🔴 Offline"}
                        <button onClick={() => toggleDevice(device.id, device.status)}>
                            {device.status === "online" ? "Выключить" : "Включить"}
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default DeviceList;
