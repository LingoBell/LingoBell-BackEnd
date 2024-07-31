from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.models import User, ChatRoom
from app.database import SessionLocal
from pydantic import BaseModel
from typing import List, Optional


class FormData(BaseModel):
        selectedInterests: List[str]
        gender : str
        name : str
        mainLanguage : str
        learningLanguages : List[str]
        languageWithLevel : List[str]
        userIntroduce: Optional[str] = None
        nation : str

def get_user_form_data(data : FormData):
    print("formData:", data)
    return data


def get_user_list_data(db: Session):
    return db.query(User).all()

def get_request_user_list_data(db: Session, uid: str):
    user = db.query(User).filter(User.userCode == uid).first()

    if user is None:
        print(f'User with userCode {uid} not found.')
        return []
    
    print('요청받은 user의 userId', user.userId)

    stmt = (
        select(ChatRoom, User)
        .join(User, ChatRoom.userId == User.userId)
        .where(ChatRoom.partnerId == user.userId)
    )
    results = db.execute(stmt).all()

    result_list = []
    for chatrooms, users in results:
        result = {
            'chatRoomId': chatrooms.chatRoomId,
            'chatRoomName': chatrooms.chatName,
            'chatRoomDescript': chatrooms.chatRoomDescript,
            'userId': users.userId,
            'userName': users.userName,
            'userCode': users.userCode,
            'profileImages': users.profileImages,
            'description': users.description,
            'nation': users.nation,
            'email': users.email
        }
        print('결과', result)
        result_list.append(result)
        
    return result_list
