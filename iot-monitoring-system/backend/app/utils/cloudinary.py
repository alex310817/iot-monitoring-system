import cloudinary
import cloudinary.uploader
import os

# Конфигурируем Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

def upload_avatar(image):
    """Загружает изображение в Cloudinary и возвращает URL"""
    upload_result = cloudinary.uploader.upload(image)
    return upload_result["secure_url"]
