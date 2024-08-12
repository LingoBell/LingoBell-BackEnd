from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.services.partners_service import get_request_user_list_data, get_user_list_data

router = APIRouter()

@router.get("")
def get_user_list(request : Request, db: Session = Depends(get_db)):
    current_user_code = request.state.user['uid']
    user_data = get_user_list_data(db, current_user_code)
    
    if not user_data:
        raise HTTPException(status_code=404, detail="UserList not found")
    return user_data

@router.get("/requests")
def get_request_user_list(request: Request, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    print('state   ', uid)
    user_data = get_request_user_list_data(db, uid)
    if not user_data:
        raise HTTPException(status_code=404, detail="Request UserList not found")
    return user_data
