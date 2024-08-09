# # STEP 1 추론기에 필요한 패키지 가져옴
# import base64
# from typing import List
# from fastapi import HTTPException
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# import torch, cv2
# from transformers import pipeline, AutoModel, AutoTokenizer, AutoFeatureExtractor, AutoModelForSemanticSegmentation
# from huggingface_hub import hf_hub_download, snapshot_download
# from diffusers import DiffusionPipeline
# import numpy as np
# from PIL import Image

# class Landmark(BaseModel):
#     x: float
#     y: float
#     z: float
#     visibility: float

# class FaceData(BaseModel):
#     landmarks: List[Landmark]
    
# cha_image = cv2.imread('./cha.png', cv2.IMREAD_UNCHANGED)

# model_path = hf_hub_download(repo_id="FaceAdapter/FaceAdapter", filename="controlnet/diffusion_pytorch_model.bin", local_dir="./checkpoints")
# config_path = hf_hub_download(repo_id="FaceAdapter/FaceAdapter", filename="controlnet/config.json")

# # 모델 로드
# model = AutoModelForSemanticSegmentation.from_pretrained(config_path)
# model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
# model.eval()

# # 특징 추출기 로드
# feature_extractor = AutoFeatureExtractor.from_pretrained("FaceAdapter/FaceAdapter")

# # def get_face_landmark_data(face_data_model):
#     # STEP 2 추론기에 필요한 모델 가져옴 (객체 생성)

#     # print('서비스 도착 2')
#     # # STEP 3: 랜드마크 데이터를 사용하여 이미지 처리
    

#     # print('서비스 도착 3')
#     # # STEP 4: 모델 추론
    

#     # print('서비스 도착 4')
#     # # STEP 5: 출력 후처리 (필요시)

# def get_face_landmark_data(face_data_model: FaceData):
#     # FaceAdapter 모델 다운로드 및 로드
    
#     # model_path = hf_hub_download(repo_id="FaceAdapter/FaceAdapter", filename="controlnet/diffusion_pytorch_model.bin")
#     # config_path = hf_hub_download(repo_id="FaceAdapter/FaceAdapter", filename="controlnet/config.json")

#     # # 모델 로드
#     # model = AutoModelForSemanticSegmentation.from_pretrained(config_path)
#     # model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
#     # model.eval()

#     # # 특징 추출기 로드
#     # feature_extractor = AutoFeatureExtractor.from_pretrained("FaceAdapter/FaceAdapter")

#     # 얼굴 랜드마크를 이미지로 변환
#     landmark_image = landmarks_to_image(face_data_model.landmarks)

#     # 대상 얼굴 이미지 로드 (cha.png)
#     target_image = Image.open("cha.png")

#     # 입력 준비
#     inputs = feature_extractor(images=landmark_image, target_images=target_image, return_tensors="pt")

#     # 출력 생성
#     with torch.no_grad():
#         outputs = model(**inputs)

#     # 출력 처리
#     output_image = process_output(outputs, target_image)

#     # 출력 이미지를 base64로 변환
#     _, buffer = cv2.imencode('.png', output_image)
#     img_base64 = base64.b64encode(buffer).decode('utf-8')
#     print('ddddddddddddddddddddddddd',img_base64)

#     return img_base64

# def landmarks_to_image(landmarks):
#     # 빈 이미지 생성
#     img = np.zeros((512, 512, 3), dtype=np.uint8)

#     # 이미지에 랜드마크 그리기
#     for lm in landmarks:
#         x, y = int(lm.x * 512), int(lm.y * 512)
#         cv2.circle(img, (x, y), 2, (255, 255, 255), -1)

#     return Image.fromarray(img)

# def process_output(outputs, target_image):
#     # 모델의 출력에서 이미지 추출
#     output_image = outputs.logits.argmax(dim=1)[0].cpu().numpy()

#     # 출력 이미지 크기를 대상 이미지 크기에 맞게 조정
#     output_image = cv2.resize(output_image, target_image.size)

#     # 출력을 대상 이미지의 마스크로 적용
#     target_array = np.array(target_image)
#     mask = (output_image > 0).astype(np.uint8) * 255
#     result = cv2.bitwise_and(target_array, target_array, mask=mask)

#     return result