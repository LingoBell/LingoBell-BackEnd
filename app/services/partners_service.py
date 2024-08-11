from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased
from app.database.models import ChatRoom, User, UserLearningLang, Language, UserInterest, Interest, Nation
from app.database import SessionLocal

def get_user_list_data(db: Session, current_user_code : str):
    # 현재 사용자 정보를 가져옵니다.
    current_user = db.query(User).filter(User.userCode == current_user_code).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    current_user_id = current_user.userId

    LearningLangAlias = aliased(UserLearningLang)
    LanguageAlias = aliased(Language)
    InterestAlias = aliased(Interest)
    NationAlias = aliased(Nation)

    results = db.query(
        User.userId.label('userId'),
        User.userCode.label('userCode'),
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
    ).filter(
        User.userId != current_user_id #현재 사용자의 정보는 제외
    ).all()
    
    user_data = {}
    for row in results:
        user_id = row.userId
        if user_id not in user_data:
            user_data[user_id] = {
                'userId': row.userId,
                'userCode' : row.userCode,
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
        
        if(row.language is not None and row.langLevel is not None):
            # Check for duplicates before adding learning languages
            learning_language = {'language': row.language, 'langLevel': row.langLevel}
            if learning_language not in user_data[user_id]['learningLanguages']:
                user_data[user_id]['learningLanguages'].append(learning_language)

        if(row.interestName is not None):
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

    # stmt = (
    #     select(ChatRoom, User)
    #     .join(User, ChatRoom.userId == User.userId)
    #     .where(ChatRoom.partnerId == user.userId)
    # )
    # results = db.execute(stmt).all()

    # result_list = []
    # for chatrooms, users in results:
    #     result = {
    #         'chatRoomId': chatrooms.chatRoomId,
    #         'userId': users.userId,
    #         'userName': users.userName,
    #         'userCode': users.userCode,
    #         'profileImages': users.profileImages,
    #         'description': users.description,
    #         'nation': users.nation
    #     }
    #     print('결과', result)
    #     result_list.append(result)
        
    # return result_list
    LearningLangAlias = aliased(UserLearningLang)
    LanguageAlias = aliased(Language)
    InterestAlias = aliased(Interest)
    NationAlias = aliased(Nation)

    # ChatRoom 테이블과 관련된 User 데이터를 조회
    stmt = (
        select(
            ChatRoom.chatRoomId.label('chatRoomId'),
            User.userId.label('userId'),
            User.userName.label('userName'),
            User.gender.label('gender'),
            User.userCode.label('userCode'),
            User.birthday.label('birthday'),
            User.profileImages.label('profileImages'),
            User.description.label('description'),
            User.nation.label('nation'),
            LearningLangAlias.langLevel.label('langLevel'),
            LanguageAlias.language.label('language'),
            InterestAlias.interestName.label('interestName')
        )
        .join(User, ChatRoom.userId == User.userId)
        .join(LearningLangAlias, User.userId == LearningLangAlias.userId, isouter=True)
        .join(LanguageAlias, LearningLangAlias.langId == LanguageAlias.langId, isouter=True)
        .join(UserInterest, User.userId == UserInterest.userId, isouter=True)
        .join(InterestAlias, UserInterest.interestId == InterestAlias.interestId, isouter=True)
        .where(ChatRoom.partnerId == user.userId)
        .where(ChatRoom.joinStatus == 1)
    )
    results = db.execute(stmt).all()

    user_data = {}
    for row in results:
        chat_room_id = row.chatRoomId
        user_id = row.userId
        if chat_room_id not in user_data:
            user_data[chat_room_id] = {
                'chatRoomId': chat_room_id,
                'userId': row.userId,
                'userName': row.userName,
                'userCode': row.userCode,
                'birthday' : row.birthday,
                'gender': row.gender,
                'profileImages': row.profileImages,
                'description': row.description,
                'nation': row.nation,
                'learningLanguages': [],
                'interests': []
            }
        if(row.language is not None and row.langLevel is not None):
            # Check for duplicates before adding learning languages
            learning_language = {'language': row.language, 'langLevel': row.langLevel}
            if learning_language not in user_data[chat_room_id]['learningLanguages']:
                user_data[chat_room_id]['learningLanguages'].append(learning_language)
        
        if(row.interestName is not None):
            # Check for duplicates before adding interests
            if row.interestName and row.interestName not in user_data[chat_room_id]['interests']:
                user_data[chat_room_id]['interests'].append(row.interestName)
    return list(user_data.values())
