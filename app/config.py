# 데이터베이스 설정, API 키, 기타 설정 관련 파일

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")