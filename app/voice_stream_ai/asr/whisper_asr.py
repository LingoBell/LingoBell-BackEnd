import os
from app.voice_stream_ai.audio_utils import save_audio_to_file
import openai

# from src.audio_utils import save_audio_to_file

from .asr_interface import ASRInterface


class WhisperASR(ASRInterface):
    def __init__(self, **kwargs):
        self.model_name = kwargs.get("model_name", "whisper-1")

        openai.api_key = os.environ["OPENAI_API_KEY"]

    async def transcribe(self, client):
        # Save audio file from client buffer
        file_path = await save_audio_to_file(
            client.scratch_buffer, client.get_file_name()
        )

        # Prepare the audio file for OpenAI Whisper API
        with open(file_path, "rb") as audio_file:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
            )

        # Clean up the temporary audio file
        os.remove(file_path)

        # Extract transcription text
        transcription_text = response.get("text", "").strip()
        
        # Return the transcription result in a consistent format
        to_return = {
            "language": response.get("language"),
            "language_probability": None,
            "text": transcription_text,
            "words": "UNSUPPORTED_BY_OPENAI_WHISPER",
        }

        return to_return
