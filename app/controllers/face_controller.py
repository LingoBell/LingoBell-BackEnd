import base64
import io
import json
import os
import cv2
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi_socketio import SocketManager
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
import numpy as np
from pydantic import BaseModel
import urllib.parse
from app.face_swap import face_utils, utils
from fastapi_socketio import SocketManager
import socketio

router = APIRouter()

# project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# # 타겟 이미지 파일 경로를 지정합니다.
# target_img_path = os.path.join(project_root, "app", "face_swap", "Target", "jeon.jpg")

# print(f"Target image path: {target_img_path}")
# print(f"Current working directory: {os.getcwd()}")

# def load_target_image():
#     if not os.path.exists(target_img_path):
#         raise FileNotFoundError(f"Target image not found at {target_img_path}")
    
#     print(f"Attempting to load image from: {target_img_path}")
#     img = cv2.imread(target_img_path)
    
#     if img is None:
#         raise IOError(f"Failed to load image at {target_img_path}")
    
#     print(f"Image loaded successfully. Shape: {img.shape}")
#     return img

# try:
#     target_img = load_target_image()
#     print("Image loaded, attempting to get face landmark")
#     target_face_landmark = face_utils.get_face_landmark(target_img)
#     if target_face_landmark is None:
#         print("No face detected in target image")
#         raise ValueError("No face detected in target image")
#     else:
#         target_xyz_landmark_points, target_landmark_points = target_face_landmark
#         target_convexhull = cv2.convexHull(np.array(target_landmark_points))
#         print("Face landmark detected successfully")
# except Exception as e:
#     print(f"Error initializing face swap: {str(e)}")
#     target_img = None
#     target_face_landmark = None
#     target_xyz_landmark_points = None
#     target_landmark_points = None
#     target_convexhull = None

# @router.websocket("")
# async def websocket_face_swap(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             data = await websocket.receive_bytes()
            
#             # 바이트 데이터를 numpy array로 변환
#             nparr = np.frombuffer(data, np.uint8)
#             img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

#             face_landmark = face_utils.get_face_landmark(img)
#             if face_landmark is None:
#                 # 얼굴이 감지되지 않으면 원본 이미지 반환
#                 await websocket.send_bytes(data)
#                 continue

#             dest_xyz_landmark_points, dest_landmark_points = face_landmark
#             dest_convexhull = cv2.convexHull(np.array(dest_landmark_points))

#             result = face_utils.face_swapping(img, dest_landmark_points, dest_xyz_landmark_points, dest_convexhull,
#                                               target_img, target_landmark_points, target_convexhull)

#             # 결과 이미지를 바이트로 인코딩
#             _, buffer = cv2.imencode('.jpg', result)
#             jpg_as_text = base64.b64encode(buffer)

#             # 처리된 이미지를 클라이언트로 전송
#             await websocket.send_bytes(jpg_as_text)

#     except WebSocketDisconnect:
#         print("WebSocket connection closed")
#     except Exception as e:
#         print(f"Error in WebSocket connection: {str(e)}")