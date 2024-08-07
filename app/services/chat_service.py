import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, select
from datetime import datetime
from app.database.models import ChatRoom, User, UserInterest, AiRecommend, AiQuiz, Interest
from app.database import SessionLocal
from app.ai_recommendation.recommend_utils import get_topic_recommendations, get_quiz_recommendations
from app.ai_recommendation.recommend_input import UserQuizInput, UserTopicInput


def generate_partner_id_user_id_or_query(partnerId, userId):
    return or_(
            and_(ChatRoom.userId == userId, ChatRoom.partnerId == partnerId),
            and_(ChatRoom.userId == partnerId, ChatRoom.partnerId == userId)
        )

def get_live_chat_list(db: Session, uid: str):
    user = db.query(User).filter(User.userCode == uid).first()
    userId = user.userId
    
    # stmt1 = select(ChatRoom).join(User, ChatRoom.userId == User.userId).where(ChatRoom.partnerId == userId)
    # stmt2 = select(ChatRoom).join(User, ChatRoom.partnerId == User.userId).where(ChatRoom.userId == userId)
    # full_stmt = stmt1.union_all(stmt2)
    query1 = db.query(ChatRoom, User).join(User, ChatRoom.userId == User.userId).filter(ChatRoom.partnerId == userId).filter(ChatRoom.joinStatus == 2)

    # 두 번째 쿼리
    query2 = db.query(ChatRoom, User).join(User, ChatRoom.partnerId == User.userId).filter(ChatRoom.userId == userId).filter(ChatRoom.joinStatus == 2)

    # 두 쿼리를 union_all로 합침
    results = query1.union_all(query2).all()

    # 쿼리 실행
    # results = db.scalars(full_stmt).all()
    print(results)
    result_list = []
    for result in results:
        print(result.User, result.ChatRoom)
        result_dict = {
            "chatRoomId": result.ChatRoom.chatRoomId,
            "userId": result.User.userId,
            # "name": result.Use# The `name` variable is being used to store the value of
            # `result.User.name` in the `get_live_chat_list` function. This value
            # represents the name of the user associated with the chat room. It is
            # then included in the `result_dict` dictionary along with other user
            # information to be returned as part of the result list.
            'userName': result.User.userName,
            'birthday': result.User.birthday,
            'nation': result.User.nation,
            'gender': result.User.gender,
            'profileImages': result.User.profileImages,
            'nativeLanguage': result.User.nativeLanguage
            # "username": result.User.username,
            # 필요한 필드들을 추가
        }
        result_list.append(result_dict)
        print(result_list)
    return result_list

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
    
def update_live_chat_status(db: Session, chatRoomId: int):
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

def create_topic_recommendations_for_chat(db: Session, chat_room_id: int, user_code : str):
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

    #호출하는 유저에 따라 출력되는 언어가 바뀌어야함
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

    #user_content 및 partner_content로 수정해야함
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

def save_recommendations_to_db(db: Session, chat_room_id: int, user_id : int, recommendations: list):
    for recommendation in recommendations:
        ai_recommend = AiRecommend(
            chatRoomId=chat_room_id,
            userId = user_id,
            aiRecommendation=recommendation,
            aiRecommendDate=datetime.utcnow()
        )
        db.add(ai_recommend)
    db.commit()


def create_quiz_recommendations_for_chat(db: Session, chat_room_id: int, user_code : str):
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

        #호출하는 유저에 따라 출력되는 언어가 바뀌어야함
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

def save_quizzes_to_db(db: Session, chat_room_id: int, user_id : int, quizzes: list):
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
def get_recommendations_for_chat(db: Session, chat_room_id : int, user_code : str):
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

def get_quiz_for_chat(db: Session, chat_room_id : int, user_code : str):
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