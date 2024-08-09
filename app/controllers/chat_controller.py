from dotenv import load_dotenv
import os

load_dotenv()

import base64
from email.mime import audio
import io
import logging
import os
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, requests
from sqlalchemy.orm import Session
from app.services.chat_service import get_live_chat_data, create_chat_room, get_live_chat_list, update_live_chat_status, create_topic_recommendations_for_chat, create_quiz_recommendations_for_chat, get_recommendations_for_chat, get_quiz_for_chat, get_live_chat_history_data, request_chat_room_notification
from app.services.transcribe_service import transcribe_audio, translate_text, save_to_db
from app.database.models import ChatMessage
from datetime import datetime
from app.database import get_db
from app.ai_recommendation.recommend_input import UserTopicInput, UserQuizInput
from starlette.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

router = APIRouter()

GPU_SERVER_URL = os.getenv('GPU_SERVER_URL')

@router.put("/{chatRoomId}/vacancy")
def update_live_chat(chatRoomId: str, db: Session = Depends(get_db)):
    print('상태', chatRoomId)
    return update_live_chat_status(db, chatRoomId)

@router.get('/')
def get_live_chats(request: Request, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    live_chats = get_live_chat_list(db, uid)
    if not live_chats:
        raise HTTPException(status_code=404, detail="No live chats found")
    return live_chats

@router.get("/{chatRoomId}")
def get_live_chat(request : Request,chatRoomId: str, db: Session = Depends(get_db)):
    userCode = request.state.user['uid']
    chat_data = get_live_chat_history_data(db, chatRoomId, userCode)
    if chat_data is None:
        raise HTTPException(status_code=404, detail="Chat room not found")
    return chat_data

@router.post("/")
def create_live_chat(request: Request, chat_room: dict, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    return create_chat_room(db, chat_room, uid)

@router.post("/{chat_room_id}/stt")
async def create_stt(chat_room_id: str, text: str, uid: str, message_time: datetime, db: Session = Depends(get_db)):
    try:
        print(f"Received request for chat_room_id: {chat_room_id}")
        text_payload = {'stt texts': text}

        response = requests.post(f"{GPU_SERVER_URL}/{chat_room_id}/stt", json=text_payload)
        print(f"Response from GPU server: {response.status_code}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        transcription_result = response.json()
        print(f"Transcription result from GPU server: {transcription_result}")

        save_to_db(db, chat_room_id, transcription_result, message_time, uid)

        return transcription_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{chat_room_id}/translations")
def create_translation(chat_room_id: str, original_text: str, db: Session = Depends(get_db)):
    translated_text = translate_text(original_text, target='en')
    save_to_db(db, chat_room_id, original_text, translated_text)
    return {"original_text": original_text, "translated_text": translated_text}

@router.get("/{chat_room_id}/stt")
async def get_stt(chat_room_id: str, timestamp: Optional[datetime] = None, db: Session = Depends(get_db)):
    query = db.query(ChatMessage).filter(ChatMessage.chatRoomId == chat_room_id)
    if timestamp:
        query = query.filter(ChatMessage.messageTime > timestamp)
    messages = query.all()
    response_data = [
        {
            "type": "",
            "messageSenderId": message.messageSenderId,
            "originalMessage": message.originalMessage,
            "translatedMessage": message.translatedMessage
        } for message in messages
    ]
    return {"messages": response_data}

@router.get("/{chat_room_id}/translations")
def get_translations(chat_room_id: str, timestamp: Optional[datetime] = None, db: Session = Depends(get_db)):
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
def get_tts(chat_room_id: str, timestamp: datetime, db: Session = Depends(get_db)):
    pass

# AI 주제추천
@router.post("/{chat_room_id}/recommendations")
def create_recommendations(request:Request ,chat_room_id: str, db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_code = request.state.user['uid']
    recommendations = create_topic_recommendations_for_chat(db, chat_room_id, user_code)
    return recommendations

# AI 퀴즈생성
@router.post("/{chat_room_id}/quizzes")
def create_quiz(request:Request, chat_room_id: str, db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_code = request.state.user['uid']
    quiz = create_quiz_recommendations_for_chat(db, chat_room_id, user_code)
    return quiz

@router.get("/{chat_room_id}/recommendations")
def get_recommendations(request : Request, chat_room_id : str, db : Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_code = request.state.user['uid']
    recommendations = get_recommendations_for_chat(db, chat_room_id, user_code)
    if not recommendations:
        raise HTTPException(status_code=404, detail="Recommendations not found")
    return recommendations

@router.get("/{chat_room_id}/quizzes")
def get_quiz(request : Request, chat_room_id : str, db : Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_code = request.state.user['uid']
    quiz = get_quiz_for_chat(db, chat_room_id, user_code)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quizzes not found")
    return quiz

@router.get("/{chat_room_id}/info")
def get_chat_room_info_for_notification(request : Request, chat_room_id : str, db : Session = Depends(get_db)):
    uid = request.state.user['uid']
    if not uid:
        raise HTTPException(status_code=400, detail="UID is missing")
    try:
        chatInfo = request_chat_room_notification(chat_room_id, db, uid )
    
    except Exception as e:
        print('error', e)
        raise HTTPException(status_code=400, detail="Invalid chatRoom data")

