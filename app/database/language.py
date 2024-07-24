from sqlalchemy import Column, Integer, String
from app.database import Base

class Language(Base):
    __tablename__ = 'languages'

    langCode = Column(String(500), primary_key=True, index=True) # 정희님, 이거 DB에는 INT인데 Varchar타입으로 바꿈
    language = Column(String(500), nullable=False)
