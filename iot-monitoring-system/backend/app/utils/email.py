import smtplib
from email.mime.text import MIMEText
import jwt
from datetime import datetime, timedelta

# Настройки SMTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "alex310817@gmail.com"
SMTP_PASSWORD = "hxrl begr rbhr wxtd"  # Ваш пароль приложения

# Секретный ключ для JWT
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

def send_verification_email(email: str, token: str):
    msg = MIMEText(f"Ваш токен подтверждения: {token}")
    msg["Subject"] = "Подтверждение регистрации"
    msg["From"] = SMTP_USER
    msg["To"] = email

    try:
        # Подключение к серверу через SSL
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            print("Письмо успешно отправлено.")
    except smtplib.SMTPAuthenticationError:
        print("Ошибка аутентификации: проверьте правильность пароля приложения.")
    except smtplib.SMTPConnectError:
        print("Ошибка соединения с сервером. Возможно, есть проблемы с интернет-соединением.")
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")

# Генерация JWT токена для подтверждения
def create_verification_token(email: str):
    expire = datetime.utcnow() + timedelta(hours=1)  # Токен действует 1 час
    to_encode = {"email": email, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
