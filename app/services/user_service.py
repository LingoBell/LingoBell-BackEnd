from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database.models import User, UserInterest, UserLearningLang
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
            birthday = form_data['birthday'],
            gender=form_data['gender'],
            description=form_data['userIntroduce'],
            nativeLanguage = form_data['mainLanguage'],
            nation=form_data.get('nation', {}).get('value'),
            nativeLanguageCode = form_data['nativeLanguageCode']
            # profileImages = form_data_['profileImg']
        )
        db.add(user_profile)
        db.commit()
        db.refresh(user_profile)

        print('added user data')

        user = db.query(User).filter(User.userCode == uid).first()
        userId = user.userId

        for interest in form_data['selectedInterests'].values():
            interest_id = interest['interestId']
            user_interest = UserInterest(
                userId = userId,
                interestId = interest_id
            )
            db.add(user_interest)
        db.commit()
        db.refresh(user_interest)
        print('added user interest data')

        for learningLang in form_data['languageWithLevel'].values():
            langId = learningLang['langId']
            level = learningLang['level']
            user_learning_lang = UserLearningLang(
                langId = langId,
                userId = userId,
                langLevel = level
            )
            db.add(user_learning_lang)
        db.commit()
        db.refresh(user_learning_lang)
        print('added user_learning_lang data')


        return user_profile
    except Exception as e:
        db.rollback()
        print('ERROR')
        raise HTTPException(status_code=400, detail=str(e))
