from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.services.user_service import add_user_profile_data, get_user_existance

router = APIRouter()

<<<<<<< Updated upstream
=======

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

<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
@router.post("/") #유저 정보 저장
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

@router.get('/check')# 유저 존재 유무 판별
def check_first_time(request: Request, db: Session = Depends(get_db)):
    # 최초 접근 유저인지 여부 (user 테이블에 존재하는가)
    print(request.state.user.get('uid'))
    uid = request.state.user.get('uid')
    result = get_user_existance(db, uid)
    return { "result": result }
