/*
 * Board: Arduino Nano
 * Processor: ATmega328P (Old Bootloader)
 */

// Простой скетч для управления светодиодом на Arduino Nano
const int LED = 13;            // Встроенный светодиод
unsigned long lastSend = 0;    // Время последней отправки статуса
const int interval = 2000;     // Интервал отправки статуса (2 секунды)

void setup() {
  pinMode(LED, OUTPUT);        // Настраиваем пин на выход
  digitalWrite(LED, LOW);      // Выключаем светодиод
  Serial.begin(9600);         // Запускаем Serial
  delay(100);                 // Даем время на инициализацию
}

void sendStatus() {
  Serial.print("LED:");
  Serial.println(digitalRead(LED) ? "ON" : "OFF");
}

void loop() {
  // Проверяем входящие команды
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd == "on") {
      digitalWrite(LED, HIGH);
      sendStatus();
    } 
    else if (cmd == "off") {
      digitalWrite(LED, LOW);
      sendStatus();
    }
  }

  // Периодически отправляем статус
  if (millis() - lastSend >= interval) {
    sendStatus();
    lastSend = millis();
  }
}