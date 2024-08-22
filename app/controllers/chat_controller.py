from dotenv import load_dotenv
import os

load_dotenv()

from email.mime import audio
import os
import shutil
import json
import base64
import io
import soundfile as sf
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.services.chat_service import get_live_chat_data, create_chat_room, get_live_chat_list, update_live_chat_status, create_topic_recommendations_for_chat, create_quiz_recommendations_for_chat, get_recommendations_for_chat, get_quiz_for_chat, get_live_chat_history_data, request_chat_room_notification
from app.services.transcribe_service import transcribe_audio_with_openai, translate_text, save_to_db, determine_target_language
from app.database.models import ChatMessage
from datetime import datetime
from app.database import get_db
from app.ai_recommendation.recommend_input import UserTopicInput, UserQuizInput
from starlette.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, message: str, user_id: str):
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

@router.put("/{chatRoomId}/vacancy")
def update_live_chat(chatRoomId: str, db: Session = Depends(get_db)):
    print('상태', chatRoomId)
    return update_live_chat_status(db, chatRoomId)

@router.get('')
def get_live_chats(request: Request, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    
    live_chats = get_live_chat_list(db, uid)
    # if not live_chats:
        # raise HTTPException(status_code=404, detail="No live chats found")
    return live_chats

@router.get("/{chatRoomId}")
def get_live_chat(request : Request,chatRoomId: str, db: Session = Depends(get_db)):
    userCode = request.state.user['uid']
    chat_data = get_live_chat_history_data(db, chatRoomId, userCode)
    if chat_data is None:
        raise HTTPException(status_code=404, detail="Chat room not found")
    return chat_data

@router.websocket("/ws/{chat_room_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, chat_room_id: str, db: Session = Depends(get_db)):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "audio":
                audio_data = base64.b64decode(message.get("blob"))
                audio_wav_io = io.BytesIO(audio_data)
                audio_wav_io.seek(0)
                audio_chunk, _ = sf.read(audio_wav_io, dtype="float32")

                transcript = transcribe_audio_with_openai(audio_chunk)
                if transcript:
                    target_language = await determine_target_language(chat_room_id, user_id, db)
                    translation = translate_text(transcript, target=target_language)
                    save_to_db(db, chat_room_id, user_id, transcript, translation)
                    await manager.send_message(json.dumps({"transcript": transcript, "translation": translation}), user_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(user_id)

@router.post("/pst")
async def process_stt_and_translate(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        user_id = data.get("userId")
        chat_room_id = data.get("chatRoomId")
        stt_text = data.get("stt_text")

        if not user_id or not chat_room_id or not stt_text:
            raise HTTPException(status_code=400, detail="Missing userId, chatRoomId or stt_text")
        
        # 타겟 언어를 결정
        target_language = await determine_target_language(chat_room_id, user_id, db)
      
        # 텍스트 번역
        translation = translate_text(stt_text, target=target_language)
        
        # 번역된 텍스트와 STT 텍스트를 함께 DB에 저장
        save_to_db(db=db, chat_room_id=chat_room_id, user_id=user_id, original_text=stt_text, translated_text=translation)
        print("save to db 성공")
        
        return {"status": "success", "message": "STT result processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
def create_live_chat(request: Request, chat_room: dict, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    return create_chat_room(db, chat_room, uid)

# @router.get("/{chat_room_id}/stt")
# async def get_stt(chat_room_id: str, timestamp: Optional[datetime] = None, db: Session = Depends(get_db)):
#     query = db.query(ChatMessage).filter(ChatMessage.chatRoomId == chat_room_id)
#     if timestamp:
#         query = query.filter(ChatMessage.messageTime > timestamp)
#     messages = query.all()
#     response_data = [
#         {
#             "type": "",
#             "messageSenderId": message.messageSenderId,
#             "originalMessage": message.originalMessage,
#             "translatedMessage": message.translatedMessage
#         } for message in messages
#     ]
#     return {"messages": response_data}

# @router.get("/{chat_room_id}/translations")
# def get_translations(chat_room_id: str, timestamp: Optional[datetime] = None, db: Session = Depends(get_db)):
#     query = db.query(ChatMessage).filter(ChatMessage.chatRoomId == chat_room_id)
#     if timestamp:
#         query = query.filter(ChatMessage.messageTime > timestamp)
#     messages = query.all()
#     response_data = [
#         {
#             "type": "me" if message.messageSenderId == 1 else "partner",
#             "messageSenderId": message.messageSenderId,
#             "originalMessage": message.originalMessage,
#             "translatedMessage": message.translatedMessage
#         } for message in messages
#     ]
#     return {"messages": response_data}

@router.get("/{chat_room_id}/messages")
async def get_stt_and_translation(chat_room_id: str, timestamp: Optional[datetime] = None, db: Session = Depends(get_db)):
    query = db.query(ChatMessage).filter(ChatMessage.chatRoomId == chat_room_id)
    if timestamp:
        query = query.filter(ChatMessage.messageTime > timestamp)
    messages = query.all()
    response_data = [
        {
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

