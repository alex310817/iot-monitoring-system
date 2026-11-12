from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import SensorData
from app.schemas import SensorDataCreate

router = APIRouter()

@router.post("/sensor_data/")
async def create_sensor_data(sensor: SensorDataCreate, db: Session = Depends(get_db)):
    sensor_data = SensorData(**sensor.dict())
    db.add(sensor_data)
    db.commit()
    db.refresh(sensor_data)
    return sensor_data
