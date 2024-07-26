# 애플리케이션의 진입점
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes import chat_routes
import uvicorn

app = FastAPI()

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

@app.on_event("startup")
def on_startup():
    init_db()
    
app.include_router(chat_routes.router, prefix="/chats", tags=["chats"])
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)