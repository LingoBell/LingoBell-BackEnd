from fastapi import APIRouter
from app.controllers import chat_controller

router = APIRouter()

# 채팅 관련 경로를 라우터에 연결
router.include_router(chat_controller.router)
