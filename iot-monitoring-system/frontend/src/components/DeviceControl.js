import React, { useEffect, useState } from 'react';
import { fetchDevices, turnOnDevice, turnOffDevice, connectWebSocket } from '../services/api';

const DeviceControl = () => {
    const [devices, setDevices] = useState([]);
    const token = localStorage.getItem('token');

    useEffect(() => {
        const loadDevices = async () => {
            const data = await fetchDevices(token);
            setDevices(data);
        };

        loadDevices();
        const socket = connectWebSocket(setDevices);

        return () => socket.close(); // Закрываем сокет при размонтировании
    }, [token]);

    return (
        <div>
            <h2>Устройства</h2>
            <ul>
                {devices.map((device) => (
                    <li key={device.id}>
                        {device.name} - Температура: {device.temperature}°C - Влажность: {device.humidity}%
                        <button onClick={() => turnOnDevice(device.id, token)}>Включить</button>
                        <button onClick={() => turnOffDevice(device.id, token)}>Выключить</button>
                    </li>
                ))}
            </ul>
            <button onClick={() => { localStorage.removeItem('token'); window.location.reload(); }}>Выйти</button>
        </div>
    );
};

export default DeviceControl;
