# 애플리케이션의 진입점
from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, Request, HTTPException, Depends
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

app = FastAPI()
transcription_result = ""
security = HTTPBearer()

origins = [
    "http://localhost:3000",
    "http://localhost:9000",
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
                response.headers["Access-Control-Allow-Origin"] = "http://localhost:9000"
                response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, DELETE, PUT"
                response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept"
                response.headers["Access-Control-Allow-Credentials"] = "true"

                return response

        if request.url.path in ["/docs", "/openapi.json"]:
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
        # print('user_info:',user_info)

        # 2-1. 검증에 실패하면 status를 403으로 반환한다  
        if user_info is None:
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
    add_dummy_data()
    
def add_dummy_data():
    db = SessionLocal()
    dummy_data = [
    {
        'chatRoomId': 4,
        'originalMessage': 'こんにちは！はじめまして。',
        'translatedMessage': '¡Hola! Encantado de conocerte.',
        'messageTime': datetime(2024, 8, 3, 10, 0, 0),
        'messageSenderId': 5
    },
    {
        'chatRoomId': 4,
        'originalMessage': '¡Hola! Encantado de conocerte también.',
        'translatedMessage': 'こんにちは！私もはじめまして。',
        'messageTime': datetime(2024, 8, 3, 10, 0, 10),
        'messageSenderId': 6
    },
    {
        'chatRoomId': 4,
        'originalMessage': '趣味は何ですか？',
        'translatedMessage': '¿Cuáles son tus aficiones?',
        'messageTime': datetime(2024, 8, 3, 10, 1, 0),
        'messageSenderId': 5
    },
    {
        'chatRoomId': 4,
        'originalMessage': 'Me gusta bailar. ¿Y a ti?',
        'translatedMessage': '私はダンスが好きです。あなたは？',
        'messageTime': datetime(2024, 8, 3, 10, 1, 30),
        'messageSenderId': 6
    },
    {
        'chatRoomId': 4,
        'originalMessage': '私は料理が好きです。新しいレシピを試すのが楽しいです。',
        'translatedMessage': 'Me gusta cocinar. Es divertido probar nuevas recetas.',
        'messageTime': datetime(2024, 8, 3, 10, 2, 0),
        'messageSenderId': 5
    },
    {
        'chatRoomId': 4,
        'originalMessage': '¡Eso es genial! ¿Tienes alguna receta favorita?',
        'translatedMessage': 'それは素晴らしいですね！お気に入りのレシピはありますか？',
        'messageTime': datetime(2024, 8, 3, 10, 2, 30),
        'messageSenderId': 6
    },
    {
        'chatRoomId': 4,
        'originalMessage': 'はい、最近はパエリアを作るのが好きです。',
        'translatedMessage': 'Sí, recientemente me gusta hacer paella.',
        'messageTime': datetime(2024, 8, 3, 10, 3, 0),
        'messageSenderId': 5
    },
    {
        'chatRoomId': 4,
        'originalMessage': '¡Me encanta la paella! La próxima vez cocinemos juntos.',
        'translatedMessage': 'パエリアが大好きです！次回は一緒に料理しましょう。',
        'messageTime': datetime(2024, 8, 3, 10, 3, 30),
        'messageSenderId': 6
    },
    {
        'chatRoomId': 4,
        'originalMessage': 'もちろん！楽しみにしています。',
        'translatedMessage': '¡Por supuesto! Lo estoy deseando.',
        'messageTime': datetime(2024, 8, 3, 10, 4, 0),
        'messageSenderId': 5
    },
    {
        'chatRoomId': 4,
        'originalMessage': '¿Cuándo te viene bien?',
        'translatedMessage': 'いつが都合いいですか？',
        'messageTime': datetime(2024, 8, 3, 10, 4, 30),
        'messageSenderId': 6
    }
]


    for data in dummy_data:
        message = ChatMessage(
            chatRoomId=data['chatRoomId'],
            originalMessage=data['originalMessage'],
            translatedMessage=data['translatedMessage'],
            messageTime=data['messageTime'],
            messageSenderId=data['messageSenderId']
        )
        db.add(message)
    
    db.commit()
    db.close()

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

app.include_router(chat_controller.router, prefix="/api/chats", tags=["chats"])
app.include_router(user_controller.router, prefix="/api/users", tags=["users"])
app.include_router(partners_controller.router, prefix="/api/partners", tags=["partners"])
# app.include_router(face_controller.router, prefix="/api/faces", tags=["faces"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)