import axios from 'axios';

// Базовый URL API
const API_URL = 'http://127.0.0.1:8000';

// Авторизация
export const loginUser = async (username, password) => {
    const response = await axios.post(`${API_URL}/auth/login`, {
        username,
        password
    });
    return response.data;
};

// Регистрация
export const registerUser = async (username, password) => {
    const response = await axios.post(`${API_URL}/auth/register`, {
        username,
        password
    });
    return response.data;
};

// Получение списка устройств
export const fetchDevices = async (token) => {
    const response = await axios.get(`${API_URL}/devices`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
};

// Включение устройства
export const turnOnDevice = async (deviceId, token) => {
    const response = await axios.post(`${API_URL}/devices/${deviceId}/on`, {}, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
};

// Выключение устройства
export const turnOffDevice = async (deviceId, token) => {
    const response = await axios.post(`${API_URL}/devices/${deviceId}/off`, {}, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
};

// WebSocket подключение
export const connectWebSocket = (setDeviceData) => {
    const socket = new WebSocket('ws://127.0.0.1:8000/ws');

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setDeviceData(data); // Обновляем состояние устройств
    };

    return socket;
};
