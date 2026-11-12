import React, { useState, useEffect } from "react";

export default function IphoneControl() {
  const [iphoneStatus, setIphoneStatus] = useState<boolean | null>(null);
  const socketUrl = "ws://localhost:8000/ws/iphone";

  useEffect(() => {
    const socket = new WebSocket(socketUrl);

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setIphoneStatus(data.status);
    };

    return () => {
      socket.close();
    };
  }, []);

  const toggleWiFi = () => {
    const socket = new WebSocket(socketUrl);
    socket.onopen = () => {
      socket.send(JSON.stringify({ action: "toggle_wifi" }));
    };
  };

  return (
    <div style={{ marginTop: "30px" }}>
      <h3>iPhone Wi-Fi - {iphoneStatus ? "Включен ✅" : "Выключен ❌"}</h3>
      <button
        onClick={toggleWiFi}
        style={{
          padding: "10px 20px",
          backgroundColor: iphoneStatus ? "red" : "green",
          color: "white",
          border: "none",
          cursor: "pointer",
        }}
      >
        {iphoneStatus ? "Выключить Wi-Fi" : "Включить Wi-Fi"}
      </button>
    </div>
  );
}
