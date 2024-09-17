import asyncio
import json
import os
import time
import pytz
from datetime import datetime

from app.services.transcribe_service import process_stt_and_translate

from .buffering_strategy_interface import BufferingStrategyInterface

class SilenceAtEndOfChunk(BufferingStrategyInterface):
    """
    A buffering strategy that processes audio at the end of each chunk with
    silence detection.

    This class is responsible for handling audio chunks, detecting silence at
    the end of each chunk, and initiating the transcription process for the
    chunk.

    Attributes:
        client (Client): The client instance associated with this buffering
                         strategy.
        chunk_length_seconds (float): Length of each audio chunk in seconds.
        chunk_offset_seconds (float): Offset time in seconds to be considered
                                      for processing audio chunks.
    """

    def __init__(self, client, **kwargs):
        """
        Initialize the SilenceAtEndOfChunk buffering strategy.

        Args:
            client (Client): The client instance associated with this buffering
                             strategy.
            **kwargs: Additional keyword arguments, including
                      'chunk_length_seconds' and 'chunk_offset_seconds'.
        """
        self.client = client

        self.chunk_length_seconds = os.environ.get(
            "BUFFERING_CHUNK_LENGTH_SECONDS"
        )
        if not self.chunk_length_seconds:
            self.chunk_length_seconds = kwargs.get("chunk_length_seconds")
        self.chunk_length_seconds = float(self.chunk_length_seconds)

        self.chunk_offset_seconds = os.environ.get(
            "BUFFERING_CHUNK_OFFSET_SECONDS"
        )
        if not self.chunk_offset_seconds:
            self.chunk_offset_seconds = kwargs.get("chunk_offset_seconds")
        self.chunk_offset_seconds = float(self.chunk_offset_seconds)

        self.error_if_not_realtime = os.environ.get("ERROR_IF_NOT_REALTIME")
        if not self.error_if_not_realtime:
            self.error_if_not_realtime = kwargs.get(
                "error_if_not_realtime", False
            )

        self.processing_flag = False
        self.filter_words = [
                            'mbc', 
                             '기자', 
                             '뉴스', 
                             'thank you', 
                             'amara.org', 
                             'MBC', 
                             'I Love You', 
                             '오늘 영상은 여기까지입니다 감사합니다', 
                             '시청해주셔서 감사합니다.', 
                             'Thank you for watching.',
                             'That&#39;s all for today&#39;s video. Thank you.',
                             '이덕영',
                             "MBC 뉴스", 
                             "MBC뉴스", 
                             "Thank you", 
                             "감사합니다",
                             "고마워요",
                             "ご視聴ありがとうございました。",
                             "ご視聴ありがとうございました",
                             "Bye-bye.",
                             "MBC",
                             "mbc",
                             "기자",
                             "신비씨",
                             "Mmm",
                             "Mommy",
                             "字幕由Amara.org社区提供",
                             "Bye",
                             "Yeah",
                             "시청해 주셔서 감사합니다.",
                             "MBC 뉴스 이덕영입니다.",
                             "워싱턴에서 MBC 뉴스 이덕영입니다",
                             "MBC 뉴스 김수영입니다.",
                             "MBC 뉴스 박진주입니다.",
                             "MBC 뉴스 손하늘입니다.",
                             "Oh my gosh, I love you too.",
                             "I love you so much.",
                             "I love you.",
                             "I love you",
                             "신비씨 사랑합니다",
                             "KBS",
                             "kbs",
                             "Bye bye. Bye bye. Bye bye.",
                             "수고하셨습니다",
                             "시청해주셔서 감사합니다",
                             "영상",
                             "구독",
                             "좋아요",
                             "Thanks for watching!",
                             "www",
                             "다음 시간에 또 뵙도록 하겠습니다.",
                             "多謝您的觀看,再會!",
                             "여러분",
                             "Love you all.",
                             "但是現實反映了林陽明不願意",
                             "ん",
                             "날씨였습니다.",
                             "天地不可摧残",
                             "Peace",
                             "otter.ai"
                            ]
    
    def should_filter_transcription(self, text):
        """
        Check if the transcription contains any of the filter words.

        Args:
            text (str): The transcription text to check.

        Returns:
            bool: True if the text should be filtered, False otherwise.
        """
        lower_text = text.lower()
        return any(word.lower() in lower_text for word in self.filter_words)

    def process_audio(self, websocket, vad_pipeline, asr_pipeline, user_id, chat_room_id):
        """
        Process audio chunks by checking their length and scheduling
        asynchronous processing.

        This method checks if the length of the audio buffer exceeds the chunk
        length and, if so, it schedules asynchronous processing of the audio.

        Args:
            websocket: The WebSocket connection for sending transcriptions.
            vad_pipeline: The voice activity detection pipeline.
            asr_pipeline: The automatic speech recognition pipeline.
        """
        chunk_length_in_bytes = (
            self.chunk_length_seconds
            * self.client.sampling_rate
            * self.client.samples_width
        )
        if len(self.client.buffer) > chunk_length_in_bytes:
            if self.processing_flag:
                exit(
                    "Error in realtime processing: tried processing a new "
                    "chunk while the previous one was still being processed"
                )

            self.client.scratch_buffer += self.client.buffer
            self.client.buffer.clear()
            self.processing_flag = True
            # Schedule the processing in a separate task
            asyncio.create_task(
                self.process_audio_async(websocket, vad_pipeline, asr_pipeline, user_id, chat_room_id)
            )

    async def process_audio_async(self, websocket, vad_pipeline, asr_pipeline, user_id, chat_room_id):
        """
        Asynchronously process audio for activity detection and transcription.

        This method performs heavy processing, including voice activity
        detection and transcription of the audio data. It sends the
        transcription results through the WebSocket connection.

        Args:
            websocket (Websocket): The WebSocket connection for sending
                                   transcriptions.
            vad_pipeline: The voice activity detection pipeline.
            asr_pipeline: The automatic speech recognition pipeline.
        """
        start = time.time()
        vad_results = await vad_pipeline.detect_activity(self.client)

        if len(vad_results) == 0:
            self.client.scratch_buffer.clear()
            self.client.buffer.clear()
            self.processing_flag = False
            return

        last_segment_should_end_before = (
            len(self.client.scratch_buffer)
            / (self.client.sampling_rate * self.client.samples_width)
        ) - self.chunk_offset_seconds
        if vad_results[-1]["end"] < last_segment_should_end_before:
            transcription = await asr_pipeline.transcribe(self.client)

            if transcription["text"] != "" and not self.should_filter_transcription(transcription["text"]):
                end = time.time()
                print(self.client.client_id)
                transcription["processing_time"] = end - start
                transcription['chat_room_id'] = chat_room_id
                transcription['user_id'] = user_id
                                
                # Seoul time zone 설정
                seoul_tz = pytz.timezone('Asia/Seoul')
                current_time = datetime.now(seoul_tz)
                transcription['messageTime'] = current_time.isoformat()                
                                
                translation = await process_stt_and_translate(transcription["text"], chat_room_id= chat_room_id, user_id= user_id)
                transcription['translated_message'] = translation
                json_transcription = json.dumps(transcription)
                
                await self.client.server.broadcast_transcription(chat_room_id, transcription)
                # await websocket.send(json_transcription)
                print('websocket', websocket.state)
                print(f"WebSocket state: {websocket.state}")
                print(f"Client IP: {websocket.remote_address[0]}, Port: {websocket.remote_address[1]}")
            self.client.scratch_buffer.clear()
            self.client.increment_file_counter()

        self.processing_flag = False