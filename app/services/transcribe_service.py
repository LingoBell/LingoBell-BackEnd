import json
import os
from datetime import datetime
from dotenv import load_dotenv
import requests
from sqlalchemy.orm import Session
from app.database.models import ChatMessage, ChatRoom, User
from fastapi import HTTPException

load_dotenv()

def translate_text(text: str, target: str) -> str:
    url = "https://translation.googleapis.com/language/translate/v2"
    params = {
        'q': text,
        'target': target,
        'key': os.getenv("GOOGLE_API_KEY")
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
          return response.json()['data']['translations'][0]['translatedText']
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")

async def determine_target_language(chat_room_id: str, sender_id: str, db: Session):
    print(f"[DEBUG] determine_target_language called with chat_room_id={chat_room_id}, sender_id={sender_id}")
    
    try:
        chat_room_users = get_chat_room_users(db, chat_room_id)
        print(f"[DEBUG] Retrieved chat_room_users: {chat_room_users}")
    except Exception as e:
        print(f"[ERROR] Failed to retrieve chat_room_users: {e}")
        return "en"
    
    receiver_info = None
    for user in [chat_room_users["user"], chat_room_users["partner"]]:
        print(f"[DEBUG] Checking user: {user}")
        if user["userId"] != sender_id:
            receiver_info = user
            break
    
    if receiver_info is None:
        print("[ERROR] Receiver info not found, defaulting to 'en'")
        return "en"
    print(f"[DEBUG] Receiver info found: {receiver_info}")
        
    sender_native_language = None
    if chat_room_users["user"]["userId"] == sender_id:
        sender_native_language = chat_room_users["user"]["nativeLanguage"]
    else:
        sender_native_language = chat_room_users["partner"]["nativeLanguage"]
    print(f"[DEBUG] Sender native language: {sender_native_language}")

    if not sender_native_language:
        print("[ERROR] Sender native language not found, defaulting to 'en'")
        return "en"
    
    for lang in receiver_info["learningLanguages"]:
        print(f"[DEBUG] Checking if receiver is learning sender's native language: {lang}")
        if lang["language"] == sender_native_language:
            print(f"[DEBUG] Match found! Returning sender's native language: {sender_native_language}")
            return sender_native_language
    
    print("[ERROR] No matching language found, defaulting to 'en'")
    return "en"

def get_chat_room_users(db: Session, chat_room_id: str):
    chat_room = db.query(ChatRoom).filter(ChatRoom.chatRoomId == chat_room_id).first()

    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    
    user = db.query(User).filter(User.userId == chat_room.userId).first()
    partner = db.query(User).filter(User.userId == chat_room.partnerId).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not partner:
        partner = User(
            userId=-1,
            userCode="dummy",
            userName="Dummy Partner",
            nativeLanguage="English",
            nativeLanguageCode="en",
            learningLanguages=[]  # 실제 DB에 있는 필드를 불러오는 부분이 필요
        )
    
    # 여기서 user와 partner가 각각 learningLanguages 속성을 제대로 가지고 있는지 확인
    print(f"[DEBUG] User learningLanguages: {user.learningLanguages}")
    print(f"[DEBUG] Partner learningLanguages: {partner.learningLanguages}")
    
    return {
        "user": {
            "userId": user.userId,
            "userCode": user.userCode,
            "nativeLanguage": user.nativeLanguage,
            "nativeLanguageCode": user.nativeLanguageCode,
            "learningLanguages": user.learningLanguages  # 여기서 user.learningLanguages를 제대로 설정해야 함
        },
        "partner": {
            "userId": partner.userId,
            "userCode": partner.userCode,
            "nativeLanguage": partner.nativeLanguage,
            "nativeLanguageCode": partner.nativeLanguageCode,
            "learningLanguages": partner.learningLanguages  # 여기서 partner.learningLanguages를 제대로 설정해야 함
        }
    }
    
def save_to_db(db: Session, chat_room_id: str, user_id: str, original_text: str, translated_text: str):
    try:
        original_text_parsed = json.loads(original_text).get("transcription", original_text)
              
        new_message = ChatMessage(
            chatRoomId=chat_room_id,
            messageSenderId=user_id,
            originalMessage=original_text_parsed,
            translatedMessage=translated_text,
            messageTime=datetime.utcnow()
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        print(f"Message saved successfully to DB with messageId={new_message.messageId}")
    except Exception as e:
        print(f"Error saving to DB: {e}")
        db.rollback()
        raise e
