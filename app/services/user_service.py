from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database.models import User, UserInterest, UserLearningLang, Language
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
    
def get_user_profile_data(db: Session, uid: str):
    user = db.query(User).filter(User.userCode == uid).first()

    user_interests = db.query(UserInterest).filter(UserInterest.userId == user.userId).all()
    
    user_learning_langs = db.query(UserLearningLang, Language).join(
        Language, UserLearningLang.langId == Language.langId).filter(UserLearningLang.userId == user.userId).all()

    interests_list = [interest.interestId for interest in user_interests]
    learning_langs_list = [{
        'langId': lang.UserLearningLang.langId,
        'langLevel': lang.UserLearningLang.langLevel,
        'language': lang.Language.language
    } for lang in user_learning_langs]
    
    user_profile_data = {
        'userCode': user.userCode,
        'userName': user.userName,
        'birthday': user.birthday,
        'gender': user.gender,
        'description': user.description,
        'nativeLanguage': user.nativeLanguage,
        'nation': user.nation,
        'nativeLanguageCode': user.nativeLanguageCode,
        'interests': interests_list,
        'learningLanguages': learning_langs_list
    }

    print("user_profile_data", user_profile_data)
    return user_profile_data

def update_user_profile_data(db: Session, uid: str, form_data: dict):
    try:
        user_profile = db.query(User).filter(User.userCode == uid).first()
        
        if not user_profile:
            raise HTTPException(status_code=404, detail="User not found")

        # 기존 데이터 업데이트
        user_profile.userName = form_data['name']
        user_profile.birthday = form_data['birthday']
        user_profile.gender = form_data['gender']
        user_profile.description = form_data['userIntroduce']
        user_profile.nativeLanguage = form_data['mainLanguage']
        user_profile.nation = form_data.get('nation', {}).get('value')
        user_profile.nativeLanguageCode = form_data['nativeLanguageCode']
        
        db.commit()
        db.refresh(user_profile)

        print('updated user data')

        userId = user_profile.userId

        # 기존 관심사를 삭제하고 새로운 관심사 추가
        db.query(UserInterest).filter(UserInterest.userId == userId).delete()
        for interest in form_data['selectedInterests'].values():
            interest_id = interest['interestId']
            user_interest = UserInterest(
                userId=userId,
                interestId=interest_id
            )
            db.add(user_interest)
        db.commit()
        print('updated user interest data')

        # 기존 학습 언어를 삭제하고 새로운 학습 언어 추가
        db.query(UserLearningLang).filter(UserLearningLang.userId == userId).delete()
        for learningLang in form_data['languageWithLevel'].values():
            langId = learningLang['langId']
            level = learningLang['level']
            user_learning_lang = UserLearningLang(
                langId=langId,
                userId=userId,
                langLevel=level
            )
            db.add(user_learning_lang)
        db.commit()
        print('updated user_learning_lang data')

        return user_profile
    except Exception as e:
        db.rollback()
        print('ERROR:', str(e))
        raise HTTPException(status_code=400, detail=str(e))
