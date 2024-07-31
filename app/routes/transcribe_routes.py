from fastapi import APIRouter
from app.controllers import transcribe_controller

router = APIRouter()

router.include_router(transcribe_controller.router)