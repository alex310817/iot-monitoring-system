const WS_URL = "ws://localhost:8000/ws/iphone"; // Адрес WebSocket-сервера

let socket = null;

export const connectWebSocket = (onMessage) => {
  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    console.log("✅ WebSocket подключен к iPhone");
  };

  socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log("📩 Получен ответ от сервера:", message);
    if (onMessage) onMessage(message);
  };

  socket.onerror = (error) => {
    console.error("⚠️ Ошибка WebSocket:", error);
  };

  socket.onclose = () => {
    console.log("❌ WebSocket отключен");
  };
};

export const sendCommand = (action) => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    const command = JSON.stringify({ action });
    socket.send(command);
    console.log("📡 Отправлена команда:", action);
  } else {
    console.error("🚫 WebSocket не подключен!");
  }
};
