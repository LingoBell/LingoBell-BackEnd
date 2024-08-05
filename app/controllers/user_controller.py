from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.services.user_service import add_user_profile_data, get_user_existance, get_user_profile_data

router = APIRouter()


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
    print("첫 로그인인가?",result)
    return { "result": result }

@router.get('/{uid}')
def get_user_profile(request: Request, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    print("get_user_profile uid", uid)
    user_profile_data = get_user_profile_data(db, uid)
    return user_profile_data