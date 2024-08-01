# 채팅 컨트롤러

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.services.chat_service import get_live_chat_data, create_chat_room, update_live_chat_status
from app.services.transcribe_service import transcribe_audio, translate_text, save_to_db
from app.database.models import ChatMessage
from datetime import datetime
from app.database import get_db

router = APIRouter()

@router.get("/liveChat/{chat_room_id}")
def get_live_chat(chat_room_id: int, db: Session = Depends(get_db)):
    chat_data = get_live_chat_data(db, chat_room_id)
    if chat_data is None:
        raise HTTPException(status_code=404, detail="Chat room not found")
    return chat_data

@router.post("/liveChat")
def create_live_chat(request: Request, chat_room: dict, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    return create_chat_room(db, chat_room, uid)

@router.put("/liveChat/{chat_room_id}")
def update_live_chat(chat_room_id: int, db: Session = Depends(get_db)):
    return update_live_chat_status(db, chat_room_id)


@router.put("/liveChat/{chat_room_id}")
def update_live_chat(chat_room_id: int, db: Session = Depends(get_db)):
    return update_live_chat_status(db, chat_room_id)

@router.post("/{chat_room_id}/stt")
def create_stt(chat_room_id: int, db: Session = Depends(get_db)):
    transcription_result = transcribe_audio(db, chat_room_id)
    return {"transcription": transcription_result}

@router.post("/{chat_room_id}/translations")
def create_translation(chat_room_id: int, original_text: str, db: Session = Depends(get_db)):
    translated_text = translate_text(original_text, target='en')
    save_to_db(db, chat_room_id, original_text, translated_text)
    return {"original_text": original_text, "translated_text": translated_text}

@router.post("/{chat_room_id}/tts")
def create_tts(chat_room_id: int, db: Session = Depends(get_db)):
    pass

@router.get("/{chat_room_id}/stt")
def get_stt(chat_room_id: int, timestamp: datetime, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(
        ChatMessage.chatRoomId == chat_room_id,
        ChatMessage.messageTime > timestamp
    ).all()
    response_data = [
        {
            "type": "me" if message.messageSenderId == 1 else "partner",
            "messageSenderId": message.messageSenderId,
            "originalMessage": message.originalMessage
        } for message in messages if message.originalMessage
    ]
    return {"messages": response_data}

@router.get("/{chat_room_id}/translations")
def get_translations(chat_room_id: int, timestamp: datetime, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(
        ChatMessage.chatRoomId == chat_room_id,
        ChatMessage.messageTime > timestamp
    ).all()
    response_data = [
        {
            "type": "me" if message.messageSenderId == 1 else "partner",
            "messageSenderId": message.messageSenderId,
            "translatedMessage": message.translatedMessage
        } for message in messages if message.translatedMessage
    ]
    return {"messages": response_data}

@router.get("/{chat_room_id}/tts")
def get_tts(chat_room_id: int, timestamp: datetime, db: Session = Depends(get_db)):
    pass