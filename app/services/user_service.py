from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.models import User, ChatRoom, UserLearningLang
from app.database import SessionLocal



def add_user_profile_data(db : Session, uid : str, form_data : dict):    
    try:
        user_profile = User(
            userCode=uid,
            userName=form_data['name'],
            gender=form_data['gender'],
            description=form_data['userIntroduce'],
            # nation=form_data.get('nation', {}).get('label'),
            # mainLanguage=form_data['mainLanguage']
        )
        db.add(user_profile)
        db.commit()
        db.refresh(user_profile)

        user = db.query(User).filter(User.userCode == uid).first()
        
        return user_profile
    except Exception as e:
        db.rollback()
        print('ERROR')
        raise HTTPException(status_code=400, detail=str(e))
        # user_learning_language = UserLearningLang (
        #     userId=uid,
        #     langCode=
        # )


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
