const WEBSOCKET_URL = "ws://localhost:8000/ws"; // URL WebSocket сервера

export function connectWebSocket(onMessage: (data: unknown) => void) {
  const socket = new WebSocket(WEBSOCKET_URL);

  socket.onopen = () => {
    console.log("✅ WebSocket подключен");
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("📡 Новые данные:", data);
    onMessage(data); // Передаём данные в обработчик
  };

  socket.onclose = () => {
    console.log("❌ WebSocket отключен. Переподключение...");
    setTimeout(() => connectWebSocket(onMessage), 5000); // Переподключаем через 5 сек
  };

  return socket;
}
