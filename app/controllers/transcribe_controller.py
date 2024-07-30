from fastapi import APIRouter
from app.services.transcribe_service import transcribe_audio
import os


router = APIRouter()

@router.get("/start_transcription")
def start_transcription():
    transcription_result = transcribe_and_get_result()
    return {"transcription": transcription_result}

def transcribe_and_get_result():
    transcription_result = transcribe_audio()
    return transcription_result

@router.get("/get_latest_transcription")
def get_latest_transcription():
    if os.path.exists("transcription.txt"):
        with open("transcription.txt", "r") as txt_file:
            transcription = txt_file.read()
        return {"transcription": transcription}
    else:
        return {"transcription": "Transcription not found"}