from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base  # Changed from app.db.base
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    email = Column(String, unique=True, nullable=False)  # ✅ Добавляем email
    is_verified = Column(Boolean, default=False)  # ✅ Флаг верификации
    verification_token = Column(String, unique=True, nullable=True)  # ✅ Токен верификации
    is_deleted = Column(Boolean, default=False) 
    
    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    user_achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, is_active={self.is_active})>"

class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    display_name = Column(String, nullable=False, default="Пользователь")
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    background_url = Column(String, nullable=True)

    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<Profile(user_id={self.user_id}, display_name={self.display_name})>"

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Boolean, default=True) 
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    last_update = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="devices")
    sensor_data = relationship("SensorData", back_populates="device", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return f"<Device(id={self.id}, name={self.name}, status={self.status}, owner_id={self.owner_id})>"

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=True)  
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    device = relationship("Device", back_populates="sensor_data")

    def __repr__(self):
        return f"<SensorData(id={self.id}, device_id={self.device_id}, temperature={self.temperature}, humidity={self.humidity}, timestamp={self.timestamp})>"

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    icon = Column(String, nullable=False)  # Material-UI icon name
    condition_type = Column(String, nullable=False)  # devices_added, profile_updated, etc.
    condition_value = Column(Integer, nullable=False)  # Количество для выполнения

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    unlocked_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Integer, default=0)

    user = relationship("User", back_populates="user_achievements")
    achievement = relationship("Achievement")
