import json
import logging
import os
import uuid
import websockets
import json

from app.controllers.chat_controller import websocket_endpoint
from app.services.transcribe_service import process_stt_and_translate
from app.voice_stream_ai.buffering_strategy.buffering_strategies import SilenceAtEndOfChunk
from app.voice_stream_ai.client import Client

class Server:
    """
    Represents the WebSocket server for handling real-time audio transcription.

    This class manages WebSocket connections, processes incoming audio data,
    and interacts with VAD and ASR pipelines for voice activity detection and
    speech recognition.

    Attributes:
        vad_pipeline: An instance of a voice activity detection pipeline.
        asr_pipeline: An instance of an automatic speech recognition pipeline.
        host (str): Host address of the server.
        port (int): Port on which the server listens.
        sampling_rate (int): The sampling rate of audio data in Hz.
        samples_width (int): The width of each audio sample in bits.
        connected_clients (dict): A dictionary mapping client IDs to Client
                                  objects.
    """

    def __init__(
        self,
        vad_pipeline,
        asr_pipeline,
        host="0.0.0.0",
        port=8765,
        sampling_rate=16000,
        samples_width=2,
        certfile=None,
        keyfile=None,
    ):
        self.vad_pipeline = vad_pipeline
        self.asr_pipeline = asr_pipeline
        self.host = host
        self.port = port
        self.sampling_rate = sampling_rate
        self.samples_width = samples_width
        self.certfile = certfile
        self.keyfile = keyfile
        self.connected_clients = {}
        self.chat_rooms = {}

    async def handle_audio(self, client, websocket):
        buffering_strategy = SilenceAtEndOfChunk(client,
                                                 chunk_length_seconds=float(os.getenv('BUFFERING_CHUNK_LENGTH_SECONDS', '1.0')),
                                                 chunk_offset_seconds=float(os.getenv('BUFFERING_CHUNK_OFFSET_SECONDS', '0.2')))
        while True:
            message = await websocket.recv()
            
            if isinstance(message, bytes):
                client.append_audio_data(message)
                buffering_strategy.process_audio(
                    websocket, 
                    self.vad_pipeline, 
                    self.asr_pipeline, 
                    client.user_id, 
                    client.chat_room_id
                )
            elif isinstance(message, str):
                config = json.loads(message)
                if config.get("type") == "config":
                    client.update_config(config["data"])
                    logging.debug(f"Updated config: {client.config}")
                    continue
            else:
                print(f"Unexpected message type from {client.client_id}")

    async def broadcast_transcription(self, chat_room_id, transcription):
        if chat_room_id in self.chat_rooms:
            for client_ws in self.chat_rooms[chat_room_id]:
                await client_ws.send(json.dumps(transcription))

    async def handle_websocket(self, websocket, path):
        client_id = str(uuid.uuid4())
        initial_message = await websocket.recv()
        config = json.loads(initial_message)
        user_id = config.get('userId')
        chat_room_id = config.get('chatRoomId')
        
        client = Client(client_id, self.sampling_rate, self.samples_width, chat_room_id, user_id)
        client.server = self
        self.connected_clients[client_id] = client

        if chat_room_id not in self.chat_rooms:
            self.chat_rooms[chat_room_id] = set()
        self.chat_rooms[chat_room_id].add(websocket)

        print(f"Client {client_id} (User {user_id}) connected to chat room {chat_room_id}")

        try:
            await self.handle_audio(client, websocket)
        except websockets.ConnectionClosed as e:
            print(f"Connection with {client_id} closed: {e}")
        finally:
            del self.connected_clients[client_id]
            self.chat_rooms[chat_room_id].remove(websocket)
            print("커넥션 종료")
            if not self.chat_rooms[chat_room_id]:
                del self.chat_rooms[chat_room_id]

    def start(self):
        return websockets.serve(
            self.handle_websocket, self.host, self.port
        )