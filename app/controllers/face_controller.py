from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
# from app.services.face_serveice import get_face_landmark_data
import cv2
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
import socketio
from typing import List

router = APIRouter()

# 얼굴 랜드마크 모델 정의
class Landmark(BaseModel):
    x: float
    y: float
    z: float
    visibility: float

class FaceData(BaseModel):
    landmarks: List[Landmark]

@router.post("/")
async def get_face_landmark(request: Request):
    # face_data = await request.json()
    # print('백 도착!!!!', face_data)
    # result = get_face_landmark_data(face_data)
    # return result
    try:
        face_data = await request.json()
        face_data_model = FaceData(landmarks=face_data)
        # print('백 도착!!!!', face_data_model)
        # 이런형식임 landmarks=[
        #   Landmark(
        #       x=0.4252014756202698, y=0.8242746591567993, z=-0.0051723988726735115, visibility=0.0)
        #       ),
        #   Landmark(x, y, z, visibility),...
        # ]
        # result = get_face_landmark_data(face_data_model)
        # return JSONResponse(content={"result": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))