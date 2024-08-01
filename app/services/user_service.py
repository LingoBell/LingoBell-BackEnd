from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database.models import User
from app.database import SessionLocal

#유저 존재 유무 판별
def get_user_existance(db: Session, uid):
    user = db.query(User).filter(User.userCode == uid).first()
    print(user)
    if user is not None:
        return 2 #기존 유저
    else:
        return 3 #신규 유저 (회원등록을 한번도 하지 않은)

def add_user_profile_data(db : Session, uid : str, form_data : dict):    
    try:
        user_profile = User(
            userCode=uid,
            userName=form_data['name'],
            # birthday = form_data['birtday'],
            gender=form_data['gender'],
            description=form_data['userIntroduce'],
            # nativeLanguage = form_data['nativeLanguage']
            # nation=form_data.get('nation', {}).get('label')

            # profileImages = form_data_['profileImg']
        )
        db.add(user_profile)
        db.commit()
        db.refresh(user_profile)

       
        print('success db')
        user = db.query(User).filter(User.userCode == uid).first()
        print('user!!:',user)

        user_learning_language = UserLearningLang(
            langLevel = form_data['레벨값'],
            langId = form_data['언어아이디'],
            userId = user.userId
        )

        return user_profile
    except Exception as e:
        db.rollback()
        print('ERROR')
        raise HTTPException(status_code=400, detail=str(e))
