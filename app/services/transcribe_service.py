import io
import os
import speech_recognition as sr
import whisper
from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
import requests
from sqlalchemy.orm import Session
from app.database import get_db
from app.database.models import ChatMessage

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def transcribe_audio(db: Session, model_name="base", non_english=True, energy_threshold=300, record_timeout=2.0, phrase_timeout=3.0):
    model = model_name
    if model_name != "large" and not non_english:
        model = model + ".en"
    audio_model = whisper.load_model(model)

    temp_file = NamedTemporaryFile().name
    transcription = ['']
    phrase_time = None
    last_sample = bytes()
    data_queue = Queue()

    recorder = sr.Recognizer()
    recorder.energy_threshold = energy_threshold
    recorder.dynamic_energy_threshold = False

    source = sr.Microphone(sample_rate=16000)
    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio: sr.AudioData) -> None:
        data = audio.get_raw_data()
        data_queue.put(data)

    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)
    print("Model loaded.\n")

    while True:
        try:
            now = datetime.utcnow()
            if not data_queue.empty():
                phrase_complete = False
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    last_sample = bytes()
                    phrase_complete = True
                phrase_time = now

                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                wav_data = io.BytesIO(audio_data.get_wav_data())

                with open(temp_file, 'w+b') as f:
                    f.write(wav_data.read())

                result = audio_model.transcribe(temp_file)
                text = result['text'].strip()

                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] = text

                os.system('cls' if os.name == 'nt' else 'clear')
                for line in transcription:
                    print(line)
                print('', end='', flush=True)

                translated_text = translate_text(text, target='en')
                save_to_db(db, text, translated_text)

        except KeyboardInterrupt:
            break

    final_transcription = "\n".join(transcription)
    return final_transcription

def translate_text(text, target):
    url = "https://translation.googleapis.com/language/translate/v2"
    params = {
        'q': text,
        'target': target,
        'key': GOOGLE_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
          return response.json()['data']['translations'][0]['translatedText']
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")
    
def save_to_db(db: Session, original_message: str, translated_message: str):
    new_message = ChatMessage(
        originalMessage=original_message,
        translatedMessage=translated_message,
        messageSenderId=1,  # userCode로 변경해야함. 일단은 1로 박아놓음.
        messageTime=datetime.utcnow(),
        chatRoomId=32  
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)