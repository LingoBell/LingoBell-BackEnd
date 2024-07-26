# 채팅 컨트롤러

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.chat_service import get_live_chat_data, create_chat_room
from app.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/liveChat/{chat_room_id}")
def get_live_chat(chat_room_id: int, db: Session = Depends(get_db)):
    chat_data = get_live_chat_data(db, chat_room_id)
    if chat_data is None:
        raise HTTPException(status_code=404, detail="Chat room not found")
    return chat_data

@router.post("/liveChat/")
def create_live_chat(chat_room: dict, db: Session = Depends(get_db)):
    return create_chat_room(db, chat_room)