from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import User, Profile
from app.schemas import ProfileUpdate
from app.database import get_db
from app.routes.auth_routes import get_current_user
from datetime import datetime  # Add this import
import logging
import shutil
import os
from app.routes.achievement_routes import check_achievements

router = APIRouter()

UPLOAD_DIR = "uploads/avatars"
BACKGROUNDS_DIR = "uploads/backgrounds"

for directory in [UPLOAD_DIR, BACKGROUNDS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

@router.get("/me")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get user profile
        result = await db.execute(
            select(Profile).where(Profile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            # Create default profile if not exists
            profile = Profile(
                user_id=current_user.id,
                display_name=current_user.username
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)

        return {
            "email": current_user.email,
            "display_name": profile.display_name,
            "bio": profile.bio,
            "avatar_url": profile.avatar_url,
            "background_url": profile.background_url  # Add this line
        }

    except Exception as e:
        logging.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при получении профиля")

@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Profile).where(Profile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = Profile(user_id=current_user.id)
            db.add(profile)

        # Update profile fields
        profile.display_name = profile_data.display_name
        profile.bio = profile_data.bio
        profile.avatar_url = profile_data.avatar_url

        await db.commit()
        await db.refresh(profile)

        # Check for profile-related achievements
        unlocked = await check_achievements(current_user.id, "profile_completed", db)
        
        return {
            "message": "Профиль обновлен",
            "display_name": profile.display_name,
            "bio": profile.bio,
            "avatar_url": profile.avatar_url,
            "unlocked_achievements": [
                {"name": ach.name, "icon": ach.icon} for ach in unlocked
            ]
        }

    except Exception as e:
        logging.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении профиля")

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Create unique filename
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"avatar_{current_user.id}{file_ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Save file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update user profile
        result = await db.execute(
            select(Profile).where(Profile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = Profile(user_id=current_user.id)
            db.add(profile)

        # Update avatar URL
        profile.avatar_url = f"/uploads/avatars/{filename}"
        await db.commit()

        # Check for avatar-related achievements
        unlocked = await check_achievements(current_user.id, "avatar_set", db)
        unlocked.extend(await check_achievements(current_user.id, "avatar_changed", db))

        return {
            "status": "success",
            "avatar_url": profile.avatar_url,
            "unlocked_achievements": [
                {"name": ach.name, "icon": ach.icon} for ach in unlocked
            ]
        }

    except Exception as e:
        logging.error(f"Error uploading avatar: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при загрузке аватара"
        )

@router.post("/background")
async def upload_background(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Create unique filename
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"bg_{current_user.id}{file_ext}"
        filepath = os.path.join(BACKGROUNDS_DIR, filename)

        # Save file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update user profile
        result = await db.execute(
            select(Profile).where(Profile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = Profile(user_id=current_user.id)
            db.add(profile)

        # Update background URL
        profile.background_url = f"/uploads/backgrounds/{filename}"
        await db.commit()

        return {
            "status": "success",
            "background_url": profile.background_url
        }

    except Exception as e:
        logging.error(f"Error uploading background: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при загрузке фона"
        )
