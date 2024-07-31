from fastapi import APIRouter
from app.controllers import user_controller

router = APIRouter()

# 회원 관련 경로를 라우터에 연결
router.include_router(user_controller.router)