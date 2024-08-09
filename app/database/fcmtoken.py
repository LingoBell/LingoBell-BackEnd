from sqlalchemy import Column, Integer, String
from app.database import Base

class FcmToken(Base):
    __tablename__ = 'fcmtokens'

    tokenId = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, nullable=False)
    token = Column(String(225), nullable=False)
