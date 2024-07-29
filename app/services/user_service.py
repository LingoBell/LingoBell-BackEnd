from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database.models import User
from app.database import SessionLocal

def get_user_list_data(db: Session):
    return db.query(User).all()