from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database.models import ChatRoom, User
from app.database import SessionLocal

def get_live_chat_data(db: Session, chat_room_id: int):
    return db.query(ChatRoom).filter(ChatRoom.chatRoomId == chat_room_id).first()

def create_chat_room(db: Session, chat_room: dict, uid: str):
    print("채팅방 생성 : ", chat_room)
    # print('userid', uid)
    user = db.query(User).filter(User.userCode == uid).first()
    # print('user 정보', user)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    userId = user.userId

    db_chat_room = ChatRoom(
        accessStatus=chat_room['accessStatus'],
        userId=userId,
        partnerId=chat_room['partnerId'],
    )
    db.add(db_chat_room)
    db.commit()
    db.refresh(db_chat_room)
    # print("chatRoomId", db_chat_room.chatRoomId)
    return {"chatRoomId": db_chat_room.chatRoomId}

def update_live_chat_status(db: Session, chatRoomId: int):
    # print('상태 변경할 채팅방 id : ', chatRoomId)
    chat_room = db.query(ChatRoom).filter(ChatRoom.chatRoomId == chatRoomId).first()
    chat_room.joinStatus = 2
    db.commit()
    # print("update된 chat_room", chat_room)
    return {"message" : "chatroom joinstatus updated"}

