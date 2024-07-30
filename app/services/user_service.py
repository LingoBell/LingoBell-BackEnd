from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database.models import User, ChatRoom
from app.database import SessionLocal

def get_user_list_data(db: Session):
    return db.query(User).all()

def get_request_user_list_data(db: Session, uid: str):
    user = db.query(User).filter(User.userCode == uid).first()

    if user is None:
        print(f'User with userCode {uid} not found.')
        return []
    
    print('요청받은 user의 userId', user.userId)

    chat_rooms = db.query(ChatRoom).filter(
        ChatRoom.partnerId == user.userId,
        ChatRoom.joinStatus == 1
    ).all()
    
    if not chat_rooms:
        print(f'No chat rooms found for partnerId {user.userId}.')
        return []
    
    user_ids = [chat_room.userId for chat_room in chat_rooms]
    related_users = db.query(User).filter(User.userId.in_(user_ids)).all()

    results = []
    for chat_room in chat_rooms:
        related_users = next((user for user in related_users if user.userId == chat_room.userId), None)
        if related_users:
            results.append({
                'chatRoomId': chat_room.chatRoomId,
                'chatRoomName': chat_room.chatName,
                'chatRoomDescript': chat_room.chatRoomDescript,
                'userId': related_users.userId,
                'userName': related_users.userName,
                'userCode': related_users.userCode,
                'profileImages': related_users.profileImages,
                'description': related_users.description,
                'nation': related_users.nation,
                'email': related_users.email
            })

    return results