# 비즈니스 로직을 처리하는 서비스 레이어

from sqlalchemy.orm import Session
from app.database.models import ChatRoom
from app.database import SessionLocal

def get_live_chat_data(db: Session, chat_room_id: int):
    return db.query(ChatRoom).filter(ChatRoom.chatRoomId == chat_room_id).first()

def create_chat_room(db: Session, chat_room: dict):
    print("sdklfjslkdjfkjsadlfkjsdklfj")
    print("chat_room", chat_room)
    db_chat_room = ChatRoom(
        accessStatus=chat_room['accessStatus'],
        chatName=chat_room['chatName'],
        chatRoomDescript=chat_room['chatRoomDescript'],
        chatContents=chat_room['chatContents'].encode('utf-8'),  # BLOB 타입으로 변환
        userId=chat_room['userId'],
        partnerId=chat_room['partnerId'],
    )
    print("db_chat_room", db_chat_room)
    db.add(db_chat_room)
    db.commit()
    db.refresh(db_chat_room)
    return db_chat_room