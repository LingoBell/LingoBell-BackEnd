from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database.models import ChatRoom, User, UserInterest, AiRecommend, AiQuiz, Interest
from app.database import SessionLocal
from app.ai_recommendation.recommend_utils import get_topic_recommendations, get_quiz_recommendations
from app.ai_recommendation.recommend_input import UserQuizInput, UserTopicInput


def get_live_chat_data(db: Session, chat_room_id: int):
    return db.query(ChatRoom).filter(ChatRoom.chatRoomId == chat_room_id).first()

def create_chat_room(db: Session, chat_room: dict, uid: str):
    print("채팅방 생성 : ", chat_room)
    print('userid', uid)
    user = db.query(User).filter(User.userCode == uid).first()
    print('user 정보', user)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    userId = user.userId

    db_chat_room = ChatRoom(
        accessStatus=chat_room['accessStatus'],
        userId=userId,
        partnerId=chat_room['partnerId'],
    )
    db.add(db_chat_room)
    db.commit()
    db.refresh(db_chat_room)
    print("chatRoomId", db_chat_room.chatRoomId)
    return {"chatRoomId": db_chat_room.chatRoomId}

def update_live_chat_status(db: Session, chat_room_id: int):
    print('상태 변경할 채팅방 id : ', chat_room_id)
    chat_room = db.query(ChatRoom).filter(ChatRoom.chatRoomId == chat_room_id).update({"joinStatus": 2})
    db.commit()
    print("update된 chat_room", chat_room)

#ai 추천 service layer
def get_user_interests(db: Session, user_id: int):
    user_interests = db.query(UserInterest).filter(UserInterest.userId == user_id).all()
    interest_names = [db.query(Interest).filter(Interest.interestId == interest.interestId).first().interestName for interest in user_interests]
    return interest_names

def get_topic_recommendations_for_chat(db: Session, chat_room_id: int):
    chat_room = get_live_chat_data(db, chat_room_id)
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    user = db.query(User).filter(User.userId == chat_room.userId).first()
    partner = db.query(User).filter(User.userId == chat_room.partnerId).first()

    if not user or not partner:
        raise HTTPException(status_code=404, detail="User or Partner not found")

    user_interests = get_user_interests(db, user.userId)
    partner_interests = get_user_interests(db, partner.userId)

    #user_content 및 partner_content로 수정해야함
    user_a_content = "Hi!"
    user_b_content = "Hello!"

    user_input = UserTopicInput(
        user_a_content=user_a_content,
        user_b_content=user_b_content,
        user_a_interests=user_interests,
        user_b_interests=partner_interests,
        user_a_lang=user.nativeLanguageCode,
        user_b_lang=partner.nativeLanguageCode
    )

    recommendations = get_topic_recommendations(user_input)

    save_recommendations_to_db(db, chat_room_id, recommendations["user_a_recommend"])
    return recommendations

def save_recommendations_to_db(db: Session, chat_room_id: int, recommendations: list):
    for recommendation in recommendations:
        ai_recommend = AiRecommend(
            chatRoomId=chat_room_id,
            aiRecommendation=recommendation,
            aiRecommendDate=datetime.utcnow()
        )
        db.add(ai_recommend)
    db.commit()


def get_quiz_recommendations_for_chat(db: Session, chat_room_id: int):
    chat_room = get_live_chat_data(db, chat_room_id)
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    user = db.query(User).filter(User.userId == chat_room.userId).first()
    partner = db.query(User).filter(User.userId == chat_room.partnerId).first()

    if not user or not partner:
        raise HTTPException(status_code=404, detail="User or Partner not found")

    user_interests = get_user_interests(db, user.userId)

    user_input = UserQuizInput(
        user_a_lang=user.nativeLanguageCode,
        user_b_lang=partner.nativeLanguageCode,
        user_a_interests=user_interests
    )

    quiz = get_quiz_recommendations(user_input)
    
    save_quizzes_to_db(db, chat_room_id, quiz["user_a_quiz"])
    return quiz

def save_quizzes_to_db(db: Session, chat_room_id: int, quizzes: list):
    for quiz in quizzes:
        ai_quiz = AiQuiz(
            chatRoomId=chat_room_id,
            aiQuestion=quiz["quiz"]["question"],
            aiAnswer=quiz["quiz"]["answer"],
            aiReason=quiz["quiz"]["reason"],
            aiQuizDate=datetime.utcnow()
        )
        db.add(ai_quiz)
    db.commit()


