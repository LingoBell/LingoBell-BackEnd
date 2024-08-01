from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.services.chat_service import get_live_chat_data, create_chat_room, update_live_chat_status
from app.database import SessionLocal, get_db

router = APIRouter()

@router.get("/{chatRoomId}")
def get_live_chat(chat_room_id: int, db: Session = Depends(get_db)):
    chat_data = get_live_chat_data(db, chat_room_id)
    if chat_data is None:
        raise HTTPException(status_code=404, detail="Chat room not found")
    return chat_data

@router.post("/")
def create_live_chat(request: Request, chat_room: dict, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    return create_chat_room(db, chat_room, uid)

@router.put("/{chatRoomId}/vacancy")
def update_live_chat(chat_room_id: int, db: Session = Depends(get_db)):
    return update_live_chat_status(db, chat_room_id)