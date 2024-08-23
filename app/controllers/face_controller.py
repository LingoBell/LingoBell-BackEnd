import base64
import json
import cv2
from fastapi.responses import JSONResponse
from fastapi_socketio import SocketManager
from fastapi import APIRouter, File, Query, UploadFile
import numpy as np
from pydantic import BaseModel
import urllib.parse
from app.face_swap import face_utils, utils
from fastapi_socketio import SocketManager
import socketio

router = APIRouter()

@router.post("")
async def create_face_swap(file: UploadFile = File(...)):
    print('face_controller 도착@@@@@@@@@@@@@@')
    try:
        # 이미지를 바이트로 읽기
        image_bytes = await file.read()
        np_arr = np.frombuffer(image_bytes, np.uint8)

        # OpenCV를 사용하여 이미지를 디코딩
        dest_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if dest_img is None:
            return JSONResponse(content={"error": "Invalid image data"}, status_code=400)
        
        # 대상 이미지 (스왑할 이미지)
        target_img_path = "Target/jeon.jpg"
        target_img = cv2.imread(target_img_path)
        if target_img is None:
            return JSONResponse(content={"error": "Failed to load target image"}, status_code=500)

        # 얼굴 스왑 처리
        face_landmark = face_utils.get_face_landmark(target_img)
        if face_landmark is None:
            return JSONResponse(content={"error": "No face detected in target image"}, status_code=400)

        xyz_landmark_points, target_landmark_points = face_landmark
        target_convexhull = cv2.convexHull(np.array(target_landmark_points))

        face_landmark_dest = face_utils.get_face_landmark(dest_img)
        if face_landmark_dest is None:
            return JSONResponse(content={"error": "No face detected in destination image"}, status_code=400)

        dest_xyz_landmark_points, dest_landmark_points = face_landmark_dest
        dest_convexhull = cv2.convexHull(np.array(dest_landmark_points))

        # 얼굴 스왑 처리 함수 호출
        new_face, result = face_utils.face_swapping(dest_img, dest_landmark_points, dest_xyz_landmark_points,
                                                    dest_convexhull, target_img, target_landmark_points,
                                                    target_convexhull, return_face=True)

        # 결과 이미지 인코딩
        _, buffer = cv2.imencode('.jpg', result)
        result_image_bytes = buffer.tobytes()

        # 결과 반환
        return JSONResponse(content={"message": "Frame processed successfully", "processed_image": result_image_bytes})
    
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)