from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.services.user_service import add_user_profile_data

router = APIRouter()

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
    
