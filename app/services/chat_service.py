import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, select
from datetime import datetime
from app.database.models import ChatRoom, User, UserInterest, AiRecommend, AiQuiz, Interest, UserLearningLang, Language, FcmToken
from app.database import SessionLocal
from app.ai_recommendation.recommend_utils import get_topic_recommendations, get_quiz_recommendations
from app.ai_recommendation.recommend_input import UserQuizInput, UserTopicInput
from app.utils.firebase_utils import send_notification_to_user



def generate_partner_id_user_id_or_query(partnerId, userId):
    return or_(
            and_(ChatRoom.userId == userId, ChatRoom.partnerId == partnerId),
            and_(ChatRoom.userId == partnerId, ChatRoom.partnerId == userId)
        )

# def get_live_chat_list(db: Session, uid: str):
#     user = db.query(User).filter(User.userCode == uid).first()

#     if not user:
#         return None

#     userId = user.userId
    
#     joinStatus = 2

#     # stmt1 = select(ChatRoom).join(User, ChatRoom.userId == User.userId).where(ChatRoom.partnerId == userId)
#     # stmt2 = select(ChatRoom).join(User, ChatRoom.partnerId == User.userId).where(ChatRoom.userId == userId)
#     # full_stmt = stmt1.union_all(stmt2)
#     query1 = db.query(ChatRoom, User).join(User, ChatRoom.userId == User.userId).filter(ChatRoom.partnerId == userId).filter(ChatRoom.joinStatus == joinStatus)

#     # 두 번째 쿼리
#     query2 = db.query(ChatRoom, User).join(User, ChatRoom.partnerId == User.userId).filter(ChatRoom.userId == userId).filter(ChatRoom.joinStatus == joinStatus)

#     # 두 쿼리를 union_all로 합침
#     results = query1.union_all(query2).all()

#     # 쿼리 실행
#     # results = db.scalars(full_stmt).all()
#     print(results)
#     result_list = []
#     for result in results:
#         print(result.User, result.ChatRoom)
#         result_dict = {
#             "chatRoomId": result.ChatRoom.chatRoomId,
#             "userId": result.User.userId,
#             # "name": result.Use# The `name` variable is being used to store the value of
#             # `result.User.name` in the `get_live_chat_list` function. This value
#             # represents the name of the user associated with the chat room. It is
#             # then included in the `result_dict` dictionary along with other user
#             # information to be returned as part of the result list.
#             'userName': result.User.userName,
#             'birthday': result.User.birthday,
#             'nation': result.User.nation,
#             'gender': result.User.gender,
#             'profileImages': result.User.profileImages,
#             'nativeLanguage': result.User.nativeLanguage,
#             'learningLanguages' : [],
#             'interests' : [],
#             # 필요한 필드들을 추가
#         }
#         result_list.append(result_dict)
#     return result_list

def get_live_chat_list(db: Session, uid: str):
    user = db.query(User).filter(User.userCode == uid).first()

    if not user:
        return None

    userId = user.userId
    joinStatus = 2

    # 첫 번째 쿼리
    query1 = db.query(ChatRoom, User, UserLearningLang, Language, UserInterest, Interest).join(
        User, ChatRoom.userId == User.userId
    ).join(
        UserLearningLang, User.userId == UserLearningLang.userId, isouter=True
    ).join(
        Language, UserLearningLang.langId == Language.langId, isouter=True
    ).join(
        UserInterest, User.userId == UserInterest.userId, isouter=True
    ).join(
        Interest, UserInterest.interestId == Interest.interestId, isouter=True
    ).filter(
        ChatRoom.partnerId == userId
    ).filter(
        ChatRoom.joinStatus == joinStatus
    )

    # 두 번째 쿼리
    query2 = db.query(ChatRoom, User, UserLearningLang, Language, UserInterest, Interest).join(
        User, ChatRoom.partnerId == User.userId
    ).join(
        UserLearningLang, User.userId == UserLearningLang.userId, isouter=True
    ).join(
        Language, UserLearningLang.langId == Language.langId, isouter=True
    ).join(
        UserInterest, User.userId == UserInterest.userId, isouter=True
    ).join(
        Interest, UserInterest.interestId == Interest.interestId, isouter=True
    ).filter(
        ChatRoom.userId == userId
    ).filter(
        ChatRoom.joinStatus == joinStatus
    )

    # 두 쿼리를 union_all로 합침
    results = query1.union_all(query2).all()

    result_list = []
    chat_rooms = {}

    for chat_room, user, user_learning_lang, language, user_interest, interest in results:
        chat_room_id = chat_room.chatRoomId

        if chat_room_id not in chat_rooms:
            chat_rooms[chat_room_id] = {
                "chatRoomId": chat_room_id,
                "userId": user.userId,
                'userCode' : user.userCode,
                "userName": user.userName,
                "birthday": user.birthday,
                "nation": user.nation,
                "gender": user.gender,
                "profileImages": user.profileImages,
                "nativeLanguage": user.nativeLanguage,
                "learningLanguages": [],
                "interests": []
            }

        if language and user_learning_lang:
            learning_language = {'language': language.language, 'langLevel': user_learning_lang.langLevel}
            if learning_language not in chat_rooms[chat_room_id]['learningLanguages']:
                chat_rooms[chat_room_id]['learningLanguages'].append(learning_language)

        if interest and user_interest:
            if interest.interestName not in chat_rooms[chat_room_id]['interests']:
                chat_rooms[chat_room_id]['interests'].append(interest.interestName)
    return list(chat_rooms.values())

def get_live_chat_data(db: Session, chatRoomId: str):
    return db.query(ChatRoom).filter(ChatRoom.chatRoomId == chatRoomId).first()


def get_live_chat_history_data(db: Session, chatRoomId: str, userCode : str):
    # 현재 사용자의 정보를 가져옵니다.
    current_user = db.query(User).filter(User.userCode == userCode).first()
    
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_user_id = current_user.userId

    # chatRoomId에 해당하는 채팅 방을 찾습니다.
    chatRoom = db.query(ChatRoom).filter(ChatRoom.chatRoomId == chatRoomId).first()
    
    if not chatRoom:
        raise HTTPException(status_code=404, detail="Chat room not found")
    
    # 사용자가 해당 채팅방에 참여하고 있는지 확인합니다.
    if chatRoom.partnerId != current_user_id and chatRoom.userId != current_user_id:
        raise HTTPException(status_code=403, detail="User does not have access to this chat room")

    # 채팅방의 상대방 ID를 결정합니다.
    partnerId = chatRoom.partnerId if chatRoom.userId == current_user_id else chatRoom.userId

    # partnerId에 해당하는 사용자의 모든 관련 데이터를 가져옵니다.
    query = db.query(
        User,
        UserLearningLang,
        Language,
        UserInterest,
        Interest
    ).join(
        UserLearningLang, User.userId == UserLearningLang.userId, isouter=True
    ).join(
        Language, UserLearningLang.langId == Language.langId, isouter=True
    ).join(
        UserInterest, User.userId == UserInterest.userId, isouter=True
    ).join(
        Interest, UserInterest.interestId == Interest.interestId, isouter=True
    ).filter(
        User.userId == partnerId
    ).all()

    partner_data = {}
    for user, user_learning_lang, language, user_interest, interest in query:
        if not partner_data:
            partner_data = {
                "userId": user.userId,
                "userCode":user.userCode,
                "userName": user.userName,
                "birthday": user.birthday,
                "nation": user.nation,
                "gender": user.gender,
                "profileImages": user.profileImages,
                "nativeLanguage": user.nativeLanguage,
                "description" : user.description,
                "learningLanguages": [],
                "interests": []
            }

        if language and user_learning_lang:
            learning_language = {'language': language.language, 'langLevel': user_learning_lang.langLevel}
            if learning_language not in partner_data['learningLanguages']:
                partner_data['learningLanguages'].append(learning_language)

        if interest and user_interest:
            if interest.interestName not in partner_data['interests']:
                partner_data['interests'].append(interest.interestName)

    return partner_data

def create_chat_room(db: Session, chat_room: dict, uid: str):
    print("채팅방 생성 : ", chat_room)
    # print('userid', uid)
    user = db.query(User).filter(User.userCode == uid).first()
    # print('user 정보', user)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    userId = user.userId
    partnerId = chat_room['partnerId']
    # chatroom 이 존재하는 지여부를 찾아봄
    # The line `return db.scalar(stmt)` is attempting to execute the SQL statement represented by
    # `stmt` using the SQLAlchemy `scalar()` method.
    # stmt = select(ChatRoom).where(ChatRoom.chatRoomId == chat_room_id)
    # print(stmt)
    # return db.scalar(stmt)
    stmt = db.query(ChatRoom).filter(
        generate_partner_id_user_id_or_query(partnerId, userId)
    )
    print(stmt)
    chatRoom = stmt.first()
    if chatRoom is not None:
        return { 'chatRoomId': chatRoom.chatRoomId }

    ChatRoomId=create_chatroom_id(db)
    print('만든 방',ChatRoomId)
    db_chat_room = ChatRoom(
        chatRoomId=ChatRoomId,
        accessStatus=chat_room['accessStatus'],
        userId=userId,
        partnerId=chat_room['partnerId'],
    )
    db.add(db_chat_room)
    db.flush()
    db.commit()
    db.refresh(db_chat_room)
    # db.add(db_chat_room)
    # db.flush()

    return {"chatRoomId": db_chat_room.chatRoomId}

def create_chatroom_id(db: Session):
    while True:
        chatRoomId = str(uuid.uuid4())[:10]
        existing_chatroom = db.query(ChatRoom).filter(ChatRoom.chatRoomId == chatRoomId).first()
        print('랜덤 방번호 ', chatRoomId)
        print('이미 있는 방 ', existing_chatroom)
        if existing_chatroom is None:
            return chatRoomId
    
def update_live_chat_status(db: Session, chatRoomId: str):
    # print('상태 변경할 채팅방 id : ', chatRoomId)
    chat_room = db.query(ChatRoom).filter(ChatRoom.chatRoomId == chatRoomId).first()
    chat_room.joinStatus = 2
    db.commit()
    # print("update된 chat_room", chat_room)
    return {"message" : "chatroom joinstatus updated"}

#ai 추천 service layer
def get_user_interests(db: Session, user_id: int):
    user_interests = db.query(UserInterest).filter(UserInterest.userId == user_id).all()
    interest_names = [db.query(Interest).filter(Interest.interestId == interest.interestId).first().interestName for interest in user_interests]
    return interest_names

def create_topic_recommendations_for_chat(db: Session, chat_room_id: str, user_code: str):
    chat_room = get_live_chat_data(db, chat_room_id)
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    user = db.query(User).filter(User.userId == chat_room.userId).first()
    partner = db.query(User).filter(User.userId == chat_room.partnerId).first()

    if not user or not partner:
        raise HTTPException(status_code=404, detail="User or Partner not found")

    current_user = db.query(User).filter(User.userCode == user_code).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")

    user_interests = get_user_interests(db, user.userId)
    partner_interests = get_user_interests(db, partner.userId)

    if current_user.userId == user.userId:
        user_a = user
        user_b = partner
        user_a_interests = user_interests
        user_b_interests = partner_interests
    else:
        user_a = partner
        user_b = user
        user_a_interests = partner_interests
        user_b_interests = user_interests

    user_a_content = "Hi!"
    user_b_content = "Hello!"

    user_input = UserTopicInput(
        user_a_content=user_a_content,
        user_b_content=user_b_content,
        user_a_interests=user_a_interests,
        user_b_interests=user_b_interests,
        user_a_lang=user_a.nativeLanguageCode,
        user_b_lang=user_b.nativeLanguageCode,
    )

    recommendations = get_topic_recommendations(user_input)

    save_recommendations_to_db(db, chat_room_id, current_user.userId, recommendations["user_a_recommend"])
    return recommendations

def save_recommendations_to_db(db: Session, chat_room_id: str, user_id : int, recommendations: list):
    for recommendation in recommendations:
        ai_recommend = AiRecommend(
            chatRoomId=chat_room_id,
            userId = user_id,
            aiRecommendation=recommendation,
            aiRecommendDate=datetime.utcnow()
        )
        db.add(ai_recommend)
    db.commit()

def create_quiz_recommendations_for_chat(db: Session, chat_room_id: str, user_code : str):
    chat_room = get_live_chat_data(db, chat_room_id)
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    user = db.query(User).filter(User.userId == chat_room.userId).first()
    partner = db.query(User).filter(User.userId == chat_room.partnerId).first()

    if not user or not partner:
        raise HTTPException(status_code=404, detail="User or Partner not found")

    current_user = db.query(User).filter(User.userCode == user_code).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")

    user_interests = get_user_interests(db, user.userId)
    partner_interests = get_user_interests(db, partner.userId)

    # 호출하는 유저에 따라 출력되는 언어가 바뀌어야 함
    if current_user.userId == user.userId:
        user_a = user
        user_b = partner
        user_a_interests = user_interests
    else:
        user_a = partner
        user_b = user
        user_a_interests = partner_interests

    user_input = UserQuizInput(
        user_a_lang=user_a.nativeLanguageCode,
        user_b_lang=user_b.nativeLanguageCode,
        user_a_interests=user_a_interests,
    )

    quiz = get_quiz_recommendations(user_input)
    
    save_quizzes_to_db(db, chat_room_id, current_user.userId, quiz["user_a_quiz"])
    return quiz

def save_quizzes_to_db(db: Session, chat_room_id: str, user_id : int, quizzes: list):
    for quiz in quizzes:
        ai_quiz = AiQuiz(
            chatRoomId=chat_room_id,
            userId = user_id,
            aiQuestion=quiz["quiz"]["question"],
            aiAnswer=quiz["quiz"]["answer"],
            aiReason=quiz["quiz"]["reason"],
            aiQuizDate=datetime.utcnow()
        )
        db.add(ai_quiz)
    db.commit()


#ai 조회
def get_recommendations_for_chat(db: Session, chat_room_id : str, user_code : str):
    current_user = db.query(User).filter(User.userCode == user_code).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = current_user.userId

    recommendations = db.query(AiRecommend).filter(
        AiRecommend.chatRoomId == chat_room_id,
        AiRecommend.userId == user_id
    ).all()

    if not recommendations:
        return []

    return recommendations

def get_quiz_for_chat(db: Session, chat_room_id : str, user_code : str):
    current_user = db.query(User).filter(User.userCode == user_code).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = current_user.userId

    quiz = db.query(AiQuiz).filter(
        AiQuiz.chatRoomId == chat_room_id,
        AiQuiz.userId == user_id    
    ).all()

    if not quiz:
        return []

    return quiz


#FCM Notification
def request_chat_room_notification(chat_room_id : str, db:Session, uid : str ):
    user = db.query(User).filter(User.userCode == uid).first()
    userId = user.userId

    chatRoom = db.query(ChatRoom).filter(ChatRoom.chatRoomId == chat_room_id).first()

    if userId == chatRoom.userId:
        recipientId = chatRoom.partnerId
    
    elif userId == chatRoom.partnerId:
        recipientId = chatRoom.userId

    partner = db.query(User).filter(User.userId == recipientId).first()

    send_notification_to_user(
        recipientId,
        title=f'🎉{partner.userName}, {user.userName} just invites you!',
        body=f'🌍Learn {user.nativeLanguage} with {user.userName}!',
        image = 'https://storage.googleapis.com/lingobellstorage/lingobellLogo.png',
        link=f"https://www.lingobell.xyz/live-chat/{chat_room_id}",
        chat_room_id=chat_room_id,
        db=db)
