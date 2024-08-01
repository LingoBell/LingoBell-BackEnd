from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.transcribe_service import transcribe_audio
from app.database import get_db
from app.database.models import ChatMessage

router = APIRouter()

@router.get("/start")
def start_transcription(db: Session = Depends(get_db)):
    transcription_result = transcribe_audio(db)
    return {"transcription": transcription_result}

@router.get("/chatmessages")
def get_chatmessages(db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).all()
    response_data = [
        {
            "type": "me",
            "messageSenderId": message.messageSenderId,
            "originalMessage": message.originalMessage,
            "translatedMessage": message.translatedMessage
        } for message in messages
    ]
    return {"messages": response_data}