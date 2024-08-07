from dotenv import load_dotenv
import os

load_dotenv()

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
from app.services.chat_service import get_live_chat_data, create_chat_room, update_live_chat_status, get_topic_recommendations_for_chat, get_quiz_recommendations_for_chat
from app.services.transcribe_service import translate_text, save_to_db
from app.database.models import ChatMessage
from datetime import datetime
from app.database import get_db
from app.ai_recommendation.recommend_input import UserTopicInput, UserQuizInput
import requests

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

router = APIRouter()

NGROK_URL = os.getenv('NGROK_URL')

@router.put("/{chatRoomId}/vacancy")
def update_live_chat(chat_room_id: int, db: Session = Depends(get_db)):
    print('상태', chat_room_id)
    return update_live_chat_status(db, chat_room_id)

@router.get("/{chatRoomId}")
def get_live_chat(chat_room_id: int, db: Session = Depends(get_db)):
    chat_data = get_live_chat_data(db, chat_room_id)
    if chat_data is None:
        raise HTTPException(status_code=404, detail="Chat room not found")
    return chat_data

@router.post("/")
def create_live_chat(request: Request, chat_room: dict, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    return create_chat_room(db, chat_room, uid)

@router.put("/liveChat/{chat_room_id}")
def update_live_chat(chat_room_id: int, db: Session = Depends(get_db)):
    return update_live_chat_status(db, chat_room_id)

@router.post("/{chat_room_id}/stt")
async def create_stt(chat_room_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        print(f"Received file: {file.filename}, Content type: {file.content_type}")
        content = await file.read()
        print(f"File content size: {len(content)} bytes")
        
        files = {'file': (file.filename, file.file, file.content_type)}
        # 이 부분을 그냥 파이썬 실행하는게 아니라 프론트에서 GPU서버로 보내고, 텍스트 변환된 것을 
        response = requests.post(f"{NGROK_URL}", files=files)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        transcription_result = response.json()
        save_to_db(db, chat_room_id, transcription_result['text'], transcription_result['translated_text'])
        
        return transcription_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{chat_room_id}/translations")
def create_translation(chat_room_id: int, original_text: str, db: Session = Depends(get_db)):
    translated_text = translate_text(original_text, target='en')
    save_to_db(db, chat_room_id, original_text, translated_text)
    return {"original_text": original_text, "translated_text": translated_text}

@router.get("/{chat_room_id}/stt")
async def get_stt(chat_room_id: int, timestamp: Optional[datetime] = None, db: Session = Depends(get_db)):
    query = db.query(ChatMessage).filter(ChatMessage.chatRoomId == chat_room_id)
    if timestamp:
        query = query.filter(ChatMessage.messageTime > timestamp)
    messages = query.all()
    response_data = [
        {
            "type": "me" if message.messageSenderId == 1 else "partner",
            "messageSenderId": message.messageSenderId,
            "originalMessage": message.originalMessage,
            "translatedMessage": message.translatedMessage
        } for message in messages
    ]
    return {"messages": response_data}

@router.get("/{chat_room_id}/translations")
def get_translations(chat_room_id: int, timestamp: Optional[datetime] = None, db: Session = Depends(get_db)):
    query = db.query(ChatMessage).filter(ChatMessage.chatRoomId == chat_room_id)
    if timestamp:
        query = query.filter(ChatMessage.messageTime > timestamp)
    messages = query.all()
    response_data = [
        {
            "type": "me" if message.messageSenderId == 1 else "partner",
            "messageSenderId": message.messageSenderId,
            "originalMessage": message.originalMessage,
            "translatedMessage": message.translatedMessage
        } for message in messages
    ]
    return {"messages": response_data}

@router.get("/{chat_room_id}/tts")
def get_tts(chat_room_id: int, timestamp: datetime, db: Session = Depends(get_db)):
    pass



# AI 주제추천
@router.post("/{chat_room_id}/recommendations")
def create_recommendations(request:Request ,chat_room_id: int, db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_code = request.state.user['uid']
    recommendations = get_topic_recommendations_for_chat(db, chat_room_id, user_code)
    return recommendations

# AI 퀴즈생성
@router.post("/{chat_room_id}/quizzes")
def create_quiz(request:Request, chat_room_id: int, db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_code = request.state.user['uid']
    quiz = get_quiz_recommendations_for_chat(db, chat_room_id, user_code)
    return quiz
