# 채팅 컨트롤러

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.services.chat_service import get_live_chat_data, create_chat_room
from app.database import SessionLocal
from app.services.auth_service import get_user_existance

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/check-first-user')# 채팅 컨트롤러
def check_first_time(request: Request, db: Session = Depends(get_db)):
    # 최초 접근 유저인지 여부 (user 테이블에 존재하는가)
    print(request.state.user.get('uid'))
    uid = request.state.user.get('uid')
    result = get_user_existance(db, uid)
    return { "result": result }

@router.post("/profile/")
def save_profile(user: dict, db: Session = Depends(get_db)):
    return create_chat_room(db, user)