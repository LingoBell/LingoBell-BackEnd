import html
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import requests
from app.database.models import ChatMessage, ChatRoom, User, UserLearningLang, Language
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal

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
        save_to_db(db=db, chat_room_id=chat_room_id, user_id=user_id, original_text=stt_text, translated_text=translation)
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
        translated_text = response.json()['data']['translations'][0]['translatedText']
        unescaped_text = html.unescape(translated_text)
        return unescaped_text
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")

async def determine_target_language(chat_room_id: str, sender_id: str, db: Session):
    print(f"[DEBUG] determine_target_language called with chat_room_id={chat_room_id}, sender_id={sender_id}")
    
    try:
        chat_room_users = get_chat_room_users(db, chat_room_id, sender_id)
        print(f"[DEBUG] Retrieved chat_room_users: {chat_room_users}")
    except Exception as e:
        print(f"[ERROR] Failed to retrieve chat_room_users: {e}")
        return "en"
    
    # current_user와 sender_id가 일치하는지 확인하고, receiver_info를 설정합니다.
    if chat_room_users["user"]["userCode"] == sender_id:
        receiver_info = chat_room_users["partner"]
    else:
        receiver_info = chat_room_users["user"]

    print(f"[DEBUG] Receiver info: {receiver_info}")

    # 상대방의 모국어 언어 코드 가져오기
    receiver_native_language_code = receiver_info.get("nativeLanguageCode")

    if receiver_native_language_code:
        print(f"[DEBUG] Returning receiver's native language code: {receiver_native_language_code}")
        return receiver_native_language_code
    else:
        print("[INFO] Receiver's native language code not found, defaulting to 'en'")
        return "en"

def get_chat_room_users(db: Session, chat_room_id: str, current_user_id: int):
    # chat_room_id를 통해 해당 채팅방의 정보를 가져옵니다.
    chat_room = db.query(ChatRoom).filter(ChatRoom.chatRoomId == chat_room_id).first()

    # 해당 채팅방이 존재하지 않을 경우 예외를 발생시킵니다.
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    
    # DB에서 userId와 partnerId에 해당하는 사용자 정보를 가져옵니다.
    user1 = db.query(User).filter(User.userId == chat_room.userId).first()
    user2 = db.query(User).filter(User.userId == chat_room.partnerId).first()
    
    # 만약 해당 사용자가 없을 경우 예외를 발생시킵니다.
    if not user1 or not user2:
        raise HTTPException(status_code=404, detail="User not found")

    # 현재 사용자가 userId인지 partnerId인지 확인합니다.
    if current_user_id == chat_room.userId:
        current_user_info = user1
        partner_info = user2
    else:
        current_user_info = user2
        partner_info = user1
    
    # 사용자와 파트너의 학습 언어를 가져옵니다.
    user_learning_languages = db.query(UserLearningLang, Language).join(
        Language, UserLearningLang.langId == Language.langId
    ).filter(UserLearningLang.userId == current_user_info.userId).all()

    partner_learning_languages = db.query(UserLearningLang, Language).join(
        Language, UserLearningLang.langId == Language.langId
    ).filter(UserLearningLang.userId == partner_info.userId).all()

    # 사용자와 파트너 정보를 반환합니다.
    return {
        "user": {
            "userId": current_user_info.userId,
            "userCode": current_user_info.userCode,
            "nativeLanguage": current_user_info.nativeLanguage,
            "nativeLanguageCode": current_user_info.nativeLanguageCode,
            "learningLanguages": [{"language": lang.language, "langLevel": learning_lang.langLevel} for learning_lang, lang in user_learning_languages]
        },
        "partner": {
            "userId": partner_info.userId,
            "userCode": partner_info.userCode,
            "nativeLanguage": partner_info.nativeLanguage,
            "nativeLanguageCode": partner_info.nativeLanguageCode,
            "learningLanguages": [{"language": lang.language, "langLevel": learning_lang.langLevel} for learning_lang, lang in partner_learning_languages]
        }
    }
    
KST = timezone(timedelta(hours=9))
current_time_kst = datetime.now(KST)

def save_to_db(db: Session, chat_room_id: str, user_id: str, original_text: str, translated_text: str):
    try:
        new_message = ChatMessage(
            chatRoomId=chat_room_id,
            messageSenderId=user_id,
            originalMessage=original_text,
            translatedMessage=translated_text,
            messageTime=current_time_kst
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        print(f"Message saved successfully to DB with messageId={new_message.messageId}")
        
    except Exception as e:
        print(f"Error saving to DB: {e}")
        db.rollback()
        raise e