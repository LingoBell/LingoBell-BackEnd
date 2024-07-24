# 비즈니스 로직을 처리하는 서비스 레이어

from sqlalchemy.orm import Session
from app.database.models import ChatRoom
from app.database import SessionLocal

def get_live_chat_data(db: Session, chat_room_id: int):
    return db.query(ChatRoom).filter(ChatRoom.chatRoomId == chat_room_id).first()
