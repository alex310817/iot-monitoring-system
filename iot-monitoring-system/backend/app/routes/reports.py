from fastapi import APIRouter
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import SensorData
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/reports/temperature/avg")
async def average_temperature():
    db: Session = SessionLocal()
    avg_temp = db.query(SensorData).filter(
        SensorData.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).with_entities(func.avg(SensorData.temperature)).scalar()
    
    return {"average_temperature": avg_temp}
