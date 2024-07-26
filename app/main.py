# 애플리케이션의 진입점
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
# import app.credentials.firebase_config
# from app.database import init_db
# from app.routes import chat_routes
import uvicorn
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware


app = FastAPI()
security = HTTPBearer()

origins = [
    "http://localhost",
    "http://localhost:9000",
    "http://localhost:8000"
    
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
def verify_token(auth_token: str): # -> 토
    
    try:
        decoded_token = auth.verify_id_token(auth_token)
        return decoded_token
    except Exception as e:
        return False
        raise HTTPException(status_code=401, detail="Invalid ID token")

## auth middleware 
def authMiddleware(request: Request, call_next):
    # 1. 토큰을 가져온다(request.headers['Authorization'])
    # Bearer {TOKEN}
    # 1-1 토큰이 없으면 status를 403으로 반환한다  
    # 2. 토큰을 검증한다
    # 2-1. 검증에 실패하면 status를 403으로 반환한다  
    # 3. 유저 정보를 request안의 user라는 키에 넣어준다
    # 
    # 검증
    # 1. route에서 request.status.user를 해서 값을 가져올 수 있다.
    # 2. 로그인을 안한경우 status를 403으로 반환한다  
    print('middleware')

    return call_next(request)
app.add_middleware(
    authMiddleware
)

@app.on_event("startup")
def on_startup():
    # init_db()
    print('1')



# 구글 로그인 요청 endpoint
@app.post("/verify-token")
async def verify_token_endpoint(request: Request):
    data = await request.json()
    id_token = data.get('idToken')
    print(data)
    print(id_token)
    if not id_token:
        raise HTTPException(status_code=400, detail="ID token is required")
    decoded_token = verify_token(id_token)
    print(decoded_token)
    return {"message": "Token is valid", "user_id": decoded_token["uid"]}

# swagger에서 토큰 유효성 검사 test용 api
@app.post("/verify-jwt")
async def verify_jwt_endpoint(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    decoded_token = verify_token(token)
    return {"message": "Token is valid", "user_id": decoded_token["uid"]}

# Bearer 토큰을 HTTP 헤더에서 자동으로 추출하여 인증
@app.get("/secure-endpoint")
async def secure_endpoint(credentials: HTTPAuthorizationCredentials = security):
    token = credentials.credentials
    decoded_token = verify_token(token)
    user_id = decoded_token['uid']
    return {"message": "Secure endpoint", "user_id": user_id}

@app.get('/test-user-token')
async def testUserToken (request: Request):
    print(request.state.user)
    
# app.include_router(chat_routes.router, prefix="/chats", tags=["chats"])
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)