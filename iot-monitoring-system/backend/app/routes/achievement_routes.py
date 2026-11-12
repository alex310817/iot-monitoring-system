from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import text
from app.database import get_db
from app.models import Achievement, UserAchievement, User
from app.routes.auth_routes import get_current_user
from datetime import datetime

router = APIRouter(prefix="/achievements", tags=["Achievements"])

DEFAULT_ACHIEVEMENTS = [
    # Устройства
    {"name": "Первые шаги", "description": "Добавьте первое устройство", "icon": "DevicesOther", "condition_type": "devices_added", "condition_value": 1},
    {"name": "Начинающий инженер", "description": "Добавьте 5 устройств", "icon": "Engineering", "condition_type": "devices_added", "condition_value": 5},
    {"name": "Опытный техник", "description": "Добавьте 10 устройств", "icon": "BuildCircle", "condition_type": "devices_added", "condition_value": 10},
    {"name": "Мастер автоматизации", "description": "Добавьте 20 устройств", "icon": "PrecisionManufacturing", "condition_type": "devices_added", "condition_value": 20},
    
    # Управление устройствами
    {"name": "Первое включение", "description": "Включите устройство впервые", "icon": "PowerSettingsNew", "condition_type": "device_switched", "condition_value": 1},
    {"name": "Активный пользователь", "description": "Переключите устройства 50 раз", "icon": "TouchApp", "condition_type": "device_switched", "condition_value": 50},
    {"name": "Энергетик", "description": "Переключите устройства 100 раз", "icon": "Bolt", "condition_type": "device_switched", "condition_value": 100},
    
    # Профиль
    {"name": "Личность", "description": "Заполните информацию профиля", "icon": "Person", "condition_type": "profile_updated", "condition_value": 1},
    {"name": "Фотограф", "description": "Установите аватар профиля", "icon": "PhotoCamera", "condition_type": "avatar_set", "condition_value": 1},
    {"name": "Дизайнер", "description": "Установите фон профиля", "icon": "Wallpaper", "condition_type": "background_set", "condition_value": 1},
    {"name": "Стилист", "description": "Измените аватар 5 раз", "icon": "Style", "condition_type": "avatar_changed", "condition_value": 5},
    
    # Время использования
    {"name": "Новичок", "description": "Проведите в системе 1 час", "icon": "Schedule", "condition_type": "time_spent", "condition_value": 1},
    {"name": "Постоянный пользователь", "description": "Проведите в системе 24 часа", "icon": "AccessTime", "condition_type": "time_spent", "condition_value": 24},
    {"name": "Эксперт", "description": "Проведите в системе 168 часов", "icon": "AccessTimeFilled", "condition_type": "time_spent", "condition_value": 168},
    
    # Ежедневная активность
    {"name": "Ежедневный визит", "description": "Войдите в систему 7 дней подряд", "icon": "CalendarToday", "condition_type": "daily_login", "condition_value": 7},
    {"name": "Преданный пользователь", "description": "Войдите в систему 30 дней подряд", "icon": "EventAvailable", "condition_type": "daily_login", "condition_value": 30},
    
    # ...добавьте еще около 35 достижений...
]

@router.get("")  # Changed from "/achievements"
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get all achievements
    result = await db.execute(select(Achievement))
    achievements = result.scalars().all()
    
    # Get user's achievements
    result = await db.execute(
        select(UserAchievement).where(UserAchievement.user_id == current_user.id)
    )
    user_achievements = result.scalars().all()
    
    # Combine the data
    achievement_data = []
    for ach in achievements:
        user_ach = next(
            (ua for ua in user_achievements if ua.achievement_id == ach.id),
            None
        )
        achievement_data.append({
            "id": ach.id,
            "name": ach.name,
            "description": ach.description,
            "icon": ach.icon,
            "condition_value": ach.condition_value,
            "unlocked": user_ach is not None,
            "progress": user_ach.progress if user_ach else 0,
            "unlocked_at": user_ach.unlocked_at if user_ach else None
        })
    
    return achievement_data

@router.get("/locked")  # Changed from "/achievements/locked"
async def get_locked_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_filtered_achievements(current_user, db, unlocked=False)

@router.get("/unlocked")  # Changed from "/achievements/unlocked"
async def get_unlocked_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_filtered_achievements(current_user, db, unlocked=True)

async def get_filtered_achievements(user: User, db: AsyncSession, unlocked: bool):
    # Get all achievements
    result = await db.execute(select(Achievement))
    achievements = result.scalars().all()
    
    # Get user's achievements
    result = await db.execute(
        select(UserAchievement).where(UserAchievement.user_id == user.id)
    )
    user_achievements = result.scalars().all()
    
    # Filter and format achievements
    achievement_data = []
    for ach in achievements:
        user_ach = next(
            (ua for ua in user_achievements if ua.achievement_id == ach.id),
            None
        )
        is_unlocked = user_ach is not None and user_ach.progress >= ach.condition_value
        
        if is_unlocked == unlocked:  # Filter based on unlock status
            achievement_data.append({
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "icon": ach.icon,
                "condition_value": ach.condition_value,
                "unlocked": is_unlocked,
                "progress": user_ach.progress if user_ach else 0,
                "unlocked_at": user_ach.unlocked_at if user_ach and is_unlocked else None
            })
    
    return achievement_data

async def check_achievements(user_id: int, action_type: str, db: AsyncSession):
    try:
        # Get relevant achievements
        result = await db.execute(
            select(Achievement).where(Achievement.condition_type == action_type)
        )
        achievements = result.scalars().all()
        
        # Get user's achievements
        result = await db.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        user_achievements = result.scalars().all()
        
        unlocked_achievements = []
        
        for achievement in achievements:
            # Find existing user achievement or create new
            user_ach = next(
                (ua for ua in user_achievements if ua.achievement_id == achievement.id),
                None
            )
            
            if user_ach:
                # Only update progress if achievement is not already unlocked
                if not user_ach.unlocked_at:
                    old_progress = user_ach.progress
                    user_ach.progress += 1
                    
                    # Check if newly unlocked
                    if old_progress < achievement.condition_value and user_ach.progress >= achievement.condition_value:
                        unlocked_achievements.append(achievement)
                        user_ach.unlocked_at = datetime.utcnow()
            else:
                # Create new progress tracking
                user_ach = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    progress=1,
                    unlocked_at=datetime.utcnow() if achievement.condition_value == 1 else None
                )
                db.add(user_ach)
                if achievement.condition_value == 1:
                    unlocked_achievements.append(achievement)

        await db.commit()
        return unlocked_achievements
    except Exception as e:
        logger.error(f"Error checking achievements: {e}")
        await db.rollback()
        return []

@router.post("/initialize", tags=["Admin"])
async def initialize_achievements(db: AsyncSession = Depends(get_db)):
    """Initialize default achievements"""
    try:
        # Clear existing achievements
        await db.execute(text("DELETE FROM user_achievements"))
        await db.execute(text("DELETE FROM achievements"))
        await db.commit()
        
        # Add all achievements
        for ach in DEFAULT_ACHIEVEMENTS:
            new_achievement = Achievement(
                name=ach["name"],
                description=ach["description"],
                icon=ach["icon"],
                condition_type=ach["condition_type"],
                condition_value=ach["condition_value"]
            )
            db.add(new_achievement)
        
        await db.commit()
        return {"message": "Achievements initialized successfully"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
