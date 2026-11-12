from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Profile
from app.utils.cloudinary import upload_avatar
from app.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.post("/{user_id}/avatar")
def upload_profile_avatar(
    user_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Эндпоинт для загрузки аватарки"""
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own avatar")

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Загружаем аватарку в Cloudinary
    avatar_url = upload_avatar(file.file)

    # Сохраняем URL в БД
    profile.avatar_url = avatar_url
    db.commit()

    return {"avatar_url": avatar_url}
