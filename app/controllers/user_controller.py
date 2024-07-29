# 회원 컨트롤러

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.services.user_service import get_user_list_data
from app.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/partners")
def get_user_list(db: Session = Depends(get_db)):
    user_data = get_user_list_data(db)
    print('user 리스트 : ', user_data)
    if not user_data:
        raise HTTPException(status_code=404, detail="UserList not found")
    return user_data
