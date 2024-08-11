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
    chat_room_users = get_chat_room_users(db, chat_room_id)
    
    receiver_info = None
    for user in chat_room_users:
        if user["userId"] != sender_id:
            receiver_info = user
            break
        
    sender_native_language = chat_room_users['user']["nativeLanguage"] if chat_room_users['user']["userId"] == sender_id else chat_room_users['partner']["nativeLanguage"]
    
    for lang in receiver_info["learningLanguages"]:
        if lang["language"] == sender_native_language:
            return sender_native_language
    
    return "en"

def get_chat_room_users(db: Session, chat_room_id: str):
    chat_room = db.query(ChatRoom).filter(ChatRoom.chatRoomId == chat_room_id).first()

    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    
    user = db.query(User).filter(User.userId == chat_room.userId).first()
    partner = db.query(User).filter(User.userId == chat_room.partnerId).first()
    
    if not user or not partner:
        raise HTTPException(status_code=404, detail="User or partner not found")
    
    return {
        "user": {
            "userId": user.userId,
            "userCode": user.userCode,
            "nativeLanguage": user.nativeLanguage,
            "nativeLanguageCode": user.nativeLanguageCode,
            "learningLanguages": [lang for lang in user.learningLanguages]
        },
        "partner": {
            "userId": partner.userId,
            "userCode": partner.userCode,
            "nativeLanguage": partner.nativeLanguage,
            "nativeLanguageCode": partner.nativeLanguageCode,
            "learningLanguages": [lang for lang in partner.learningLanguages]
        }
    }
    
def save_to_db(db: Session, chat_room_id: str, user_id: str, original_text: str, translated_text: str):
    new_message = ChatMessage(
        chatRoomId=chat_room_id,
        messageSenderId=user_id,
        originalMessage=original_text,
        translatedMessage=translated_text,
        messageTime=datetime.utcnow()
    )
    db.add(new_message)
    db.commit()