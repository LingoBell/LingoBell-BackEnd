from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.services.user_service import add_user_profile_data, get_user_existance, get_user_profile_data, update_user_profile_data, upload_to_gcs, save_fcm_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.models import User
import os

router = APIRouter()
security = HTTPBearer()


@router.post("") #유저 정보 저장
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
        print('add_user_profile_data ERROR:', e)
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

@router.get('/my-profile')
def get_my_profile(request: Request, db: Session = Depends(get_db)):
    uid = request.state.user['uid']
    user_profile_data = get_user_profile_data(db, uid)
    return user_profile_data

@router.get('/{uid}')
def get_user_profile(request: Request, uid: str, db: Session = Depends(get_db)):
    user_profile_data = get_user_profile_data(db, uid)
    return user_profile_data

@router.put('/my-profile')
async def update_user_profile(request: Request, db: Session = Depends(get_db)):
    try:
        uid = request.state.user['uid']
        form_data = await request.json()
        updated_user_profile = update_user_profile_data(db, uid, form_data)
        return {"updated_data": updated_user_profile}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/image-upload")
async def upload_image(request: Request, image: UploadFile = File(...), db: Session = Depends(get_db)):
    uid = request.state.user['uid']

    if image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    filename = f"user_{uid}_{image.filename}"

    try:
        gcs_url = upload_to_gcs(os.getenv("GCS_BUCKET_NAME"), image, filename)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"message": "Image uploaded successfully", "url": gcs_url}


@router.post("/fcm")
async def register_fcm_token(request : Request, db : Session = Depends(get_db)):
    data = await request.json()
    token = data.get('token')
    uid = request.state.user['uid']
    print(uid)
    if not uid:
        raise HTTPException(status_code=400, detail="UID is missing")

    try:
        token = save_fcm_token(uid, token, db)
    except Exception as e:
        print('ERROR', e)
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    return {"FCM_Token" : token}

