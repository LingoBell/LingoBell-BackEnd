from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased
from app.database.models import ChatRoom, User, UserLearningLang, Language, UserInterest, Interest, Nation
from app.database import SessionLocal

def get_user_list_data(db: Session):
    LearningLangAlias = aliased(UserLearningLang)
    LanguageAlias = aliased(Language)
    InterestAlias = aliased(Interest)
    NationAlias = aliased(Nation)

    results = db.query(
        User.userId.label('userId'),
        User.userName.label('userName'),
        User.gender.label('gender'),
        User.birthday.label('birthday'),
        User.description.label('description'),
        User.nativeLanguage.label('nativeLanguage'),
        User.profileImages.label('profileImages'),
        User.nation.label('nation'),
        LearningLangAlias.langLevel.label('langLevel'),
        LanguageAlias.language.label('language'),
        InterestAlias.interestName.label('interestName')
    ).join(
        LearningLangAlias, User.userId == LearningLangAlias.userId, isouter=True
    ).join(
        LanguageAlias, LearningLangAlias.langId == LanguageAlias.langId, isouter=True
    ).join(
        UserInterest, User.userId == UserInterest.userId, isouter=True
    ).join(
        InterestAlias, UserInterest.interestId == InterestAlias.interestId, isouter=True
    ).all()
    
    user_data = {}
    
    for row in results:
        user_id = row.userId
        if user_id not in user_data:
            user_data[user_id] = {
                'userId': row.userId,
                'userName': row.userName,
                'gender': row.gender,
                'birthday' : row.birthday,
                'description': row.description,
                'nativeLanguage': row.nativeLanguage,
                'profileImages': row.profileImages,
                'nation' : row.nation,
                'learningLanguages': [],
                'interests': []
            }
        
        # Check for duplicates before adding learning languages
        learning_language = {'language': row.language, 'langLevel': row.langLevel}
        if learning_language not in user_data[user_id]['learningLanguages']:
            user_data[user_id]['learningLanguages'].append(learning_language)
        
        # Check for duplicates before adding interests
        if row.interestName and row.interestName not in user_data[user_id]['interests']:
            user_data[user_id]['interests'].append(row.interestName)
    
    return list(user_data.values())


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
            'userId': users.userId,
            'userName': users.userName,
            'userCode': users.userCode,
            'profileImages': users.profileImages,
            'description': users.description,
            'nation': users.nation
        }
        print('결과', result)
        result_list.append(result)
        
    return result_list