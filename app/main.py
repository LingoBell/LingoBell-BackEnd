# 애플리케이션의 진입점
import asyncio
from dotenv import load_dotenv

from app.voice_stream_ai.asr.asr_factory import ASRFactory
from app.voice_stream_ai.server import Server
from app.voice_stream_ai.vad.vad_factory import VADFactory
load_dotenv()
from fastapi.responses import HTMLResponse
import os
from fastapi import FastAPI, Request, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
import app.connection.firebase_config
from app.database import init_db, SessionLocal
from app.controllers import chat_controller, face_controller, user_controller, partners_controller

import uvicorn
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.database.models import ChatMessage
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi_socketio import SocketManager


app = FastAPI()

transcription_result = ""
security = HTTPBearer()

origins = [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:9000",
    "http://localhost:8080"
    # 필요한 도메인 추가
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# accessToken 검증 함수
def verify_token(auth_token: str): 
    try:
        decoded_token = auth.verify_id_token(auth_token)
        # print('decoded_token',decoded_token)
        return decoded_token
    except Exception as e:
        # return False
        print(e)
        raise HTTPException(status_code=401, detail="Invalid ID token")
    

## auth middleware 
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        if request.method == "OPTIONS":
                response = JSONResponse(status_code=200, content='CORS preflight')
                response.headers["Access-Control-Allow-Origin"] = "http://localhost:8000"
                response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, DELETE, PUT"
                response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept"
                response.headers["Access-Control-Allow-Credentials"] = "true"

                return response

        if request.url.path in ["/docs", "/openapi.json", "/api/chats/pst"]:
            return await call_next(request)
        
        if not request.url.path.startswith('/api'):
            print('test')
            return await call_next(request)
        
        # 1. 토큰을 가져온다(request.headers['Authorization'])
        auth_header = request.headers.get('Authorization')
        # 테스트용 코드(development에서만 사용가능하도록 만들어냄)
        if os.getenv('ENV') == 'development' and auth_header in [
            'JWLEE',
            'SWCHO',
            'JHKIM',
            'HWPARK'
        ]:
            request.state.user = {
                "uid": auth_header
            }
            response = await call_next(request)
            return response

        # Bearer {TOKEN}
        # 1-1 토큰이 없으면 status를 403으로 반환한다  
        if not auth_header or not auth_header.startswith('Bearer'):
            return JSONResponse(status_code=403, content={'status' : 403})
        
        token = auth_header.split(' ')[1]
        print(token)

        # 2. 토큰을 검증한다
        user_info = verify_token(token)
        print(request.url.path)
        # print('user_info:',user_info)
        
        # 2-1. 검증에 실패하면 status를 403으로 반환한다  
        if user_info is None:
            print(request.url.path)
            return JSONResponse(status_code=403, content={'status':403})

        # 3. 유저 정보를 request안의 user라는 키에 넣어준다
        request.state.user = user_info
        
        # 검증
        # 1. route에서 request.status.user를 해서 값을 가져올 수 있다.
        # 2. 로그인을 안한경우 status를 403으로 반환한다   
        response = await call_next(request)
        return response

app.add_middleware(
    AuthMiddleware
)   

@app.on_event("startup")
def on_startup():
    init_db()

# # 구글 로그인 요청 endpoint
@app.post("/api/verify-token")
async def verify_token_endpoint(request: Request):
    data = await request.json()
    id_token = data.get('idToken')
    # print(data)
    # print(id_token)
    if not id_token:
        raise HTTPException(status_code=400, detail="ID token is required")
    decoded_token = verify_token(id_token)
    # print(decoded_token)
    return {"message": "Token is valid", "user_id": decoded_token["uid"]}

# # Bearer 토큰을 HTTP 헤더에서 자동으로 추출하여 인증
# @app.get("/secure-endpoint")
# async def secure_endpoint(credentials: HTTPAuthorizationCredentials = security):
#     token = credentials.credentials
#     decoded_token = verify_token(token)
#     user_id = decoded_token['uid']
#     return {"message": "Secure endpoint", "user_id": user_id}

# # swagger에서 토큰 유효성 검사 test용 api
# @app.post("/verify-jwt")
# async def verify_jwt_endpoint(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     token = credentials.credentials
#     decoded_token = verify_token(token) 
#     return {"message": "Token is valid", "user_id": decoded_token["uid"]}

@app.get('/test-user-token')
async def testUserToken (request : Request):  # credentials: HTTPAuthorizationCredentials = Depends(security)는 --> 직접적으로 fastAPI의 의존성 주입을 통해 HTTP요청에서 'Authorization'헤더를 추출
    uid = request.state.user['uid']
    data = request.state.user
    # print(request.state.user)
    return data

# @app.post("/api/chats/pst")
# async def process_stt_and_translate(request: Request):
#                                     # , db: Session = Depends(get_db)):
#     print("쌤 죽을ㅇ너ㅏ리ㅏㅇ널")
#     try:
#         data = await request.json()
#         user_id = data.get("userId")
#         chat_room_id = data.get("chatRoomId")
#         stt_text = data.get("stt_text")
#         print("stt text", stt_text)

#         if not user_id or not chat_room_id or not stt_text:
#             raise HTTPException(status_code=400, detail="Missing userId, chatRoomId or stt_text")
        
#         """  save_to_db(db, chat_room_id, user_id, stt_text, "")
        
#         target_language = await determine_target_language(chat_room_id, user_id, db)  
      
#         translation = translate_text(stt_text, target=target_language)
        
#         save_to_db(db, chat_room_id, user_id, stt_text, translation)
#         print("save to db 성공") """
        
#         return {"status": "success", "message": "STT result processed"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



# STT 서버 설정
vad_pipeline = VADFactory.create_vad_pipeline("pyannote", auth_token="huggingface_token")
asr_pipeline = ASRFactory.create_asr_pipeline("faster_whisper", model_size="large-v3")

stt_server = Server(
    vad_pipeline,
    asr_pipeline,
    host="0.0.0.0",
    port=8765,
    sampling_rate=16000,
    samples_width=2
)

# WebSocket 엔드포인트 추가
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print('소켓 들어옴')
    await websocket.accept()
    await stt_server.handle_websocket(websocket)

@app.on_event("startup")
async def startup_event():
    # 데이터베이스 초기화
    init_db()
    
    # STT 서버 시작
    await stt_server.start()

app.include_router(chat_controller.router, prefix="/api/chats", tags=["chats"])
app.include_router(user_controller.router, prefix="/api/users", tags=["users"])
app.include_router(partners_controller.router, prefix="/api/partners", tags=["partners"])
app.mount("/", StaticFiles(directory="./dist"), name="dist")
app.include_router(face_controller.router, prefix="/api/faces", tags=["faces"])
@app.middleware("http")
async def custom_404_middleware(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 404 and not request.url.path.startswith(("/api")):
        return HTMLResponse(content=open("./dist/index.html").read(), status_code=200)
    return response 

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, loop="asyncio")