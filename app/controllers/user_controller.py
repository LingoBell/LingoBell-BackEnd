# 회원 컨트롤러

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.services.user_service import get_request_user_list_data, get_user_list_data,add_user_profile_data
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
    if not user_data:
        raise HTTPException(status_code=404, detail="UserList not found")
    return user_data

@router.get("/requestPartners")
def get_request_user_list(request: Request, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    print('state   ', uid)
    user_data = get_request_user_list_data(db, uid)
    if not user_data:
        raise HTTPException(status_code=404, detail="Request UserList not found")
    return user_data

@router.post("/setUserProfile")
async def create_user_profile(request : Request, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    if not uid:
        raise HTTPException(status_code=400, detail="UID is missing")
    try:
        form_data = await request.json()
        print('w,fewjwjwjkwek:',form_data)
        user_profile = add_user_profile_data(db, uid, form_data)
        return {"data" : user_profile}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    # print('User_Profile',form_data)
    # print('UID',request.state.user['uid'])
    
