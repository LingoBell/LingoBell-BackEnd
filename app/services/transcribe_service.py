import json
import os
from datetime import datetime
from dotenv import load_dotenv
import requests
from app.database.models import ChatMessage, ChatRoom, User, UserLearningLang, Language
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db



load_dotenv()



async def process_stt_and_translate(stt_result: str, chat_room_id: str, user_id: str):
    db = SessionLocal()
    try:
        stt_text = stt_result

        if not user_id or not chat_room_id or not stt_text:
            raise HTTPException(status_code=400, detail="Missing userId, chatRoomId or stt_text")
        
        # 타겟 언어를 결정
        target_language = await determine_target_language(chat_room_id, user_id, db)
      
        # 텍스트 번역
        translation = translate_text(stt_text, target=target_language)
        
        # 번역된 텍스트와 STT 텍스트를 함께 DB에 저장
        # save_to_db(db=db, chat_room_id=chat_room_id, user_id=user_id, original_text=stt_text, translated_text=translation)
        print("save to db 성공")
        
        return translation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    
    if chat_room_users["user"]["userId"] == sender_id:
        sender_info = chat_room_users["user"]
        receiver_info = chat_room_users["partner"]
    else:
        sender_info = chat_room_users["partner"]
        receiver_info = chat_room_users["user"]

    print(f"[DEBUG] Sender info: {sender_info}")
    print(f"[DEBUG] Receiver info: {receiver_info}")

    sender_native_language_code = sender_info["nativeLanguageCode"]
    print(f"[DEBUG] Sender native language code: {sender_native_language_code}")

    if not sender_native_language_code:
        print("[ERROR] Sender native language code not found, defaulting to 'en'")
        return "en"

    for lang in receiver_info["learningLanguages"]:
        print(f"[DEBUG] Checking if receiver is learning sender's native language code: {lang}")
        if lang["language"] == sender_native_language_code:
            print(f"[DEBUG] Match found! Returning sender's native language code: {sender_native_language_code}")
            return sender_native_language_code

    print(f"[INFO] No matching language found, defaulting to receiver's native language code: {receiver_info['nativeLanguageCode']}")
    return receiver_info['nativeLanguageCode']

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
            learningLanguages=[]
        )
    
    # User의 학습 언어를 쿼리하여 가져오기
    user_learning_languages = db.query(UserLearningLang, Language).join(
        Language, UserLearningLang.langId == Language.langId
    ).filter(UserLearningLang.userId == user.userId).all()

    partner_learning_languages = db.query(UserLearningLang, Language).join(
        Language, UserLearningLang.langId == Language.langId
    ).filter(UserLearningLang.userId == partner.userId).all()

    return {
        "user": {
            "userId": user.userId,
            "userCode": user.userCode,
            "nativeLanguage": user.nativeLanguage,
            "nativeLanguageCode": user.nativeLanguageCode,
            "learningLanguages": [{"language": lang.language, "langLevel": learning_lang.langLevel} for learning_lang, lang in user_learning_languages]
        },
        "partner": {
            "userId": partner.userId,
            "userCode": partner.userCode,
            "nativeLanguage": partner.nativeLanguage,
            "nativeLanguageCode": partner.nativeLanguageCode,
            "learningLanguages": [{"language": lang.language, "langLevel": learning_lang.langLevel} for learning_lang, lang in partner_learning_languages]
        }
    }

    
def save_to_db(db: Session, chat_room_id: str, user_id: str, original_text: str, translated_text: str):
    try:
        print("save 실행")
        # original_text_parsed = json.loads(original_text).get("transcription", original_text)
              
        new_message = ChatMessage(
            chatRoomId=chat_room_id,
            messageSenderId=user_id,
            originalMessage=original_text,
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
