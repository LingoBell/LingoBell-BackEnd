from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.database import Base

class AiRecommend(Base):
    __tablename__ = 'aiRecommend'

    aiRecommendId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chatRoomId = Column(Integer, nullable=False)
    # chatRoomId = Column(Integer, ForeignKey('chatRooms.chatRoomId'), nullable=False)
    aiRecommendation = Column(String(500), nullable=False)
    aiRecommendDate = Column(Date, nullable=False)
