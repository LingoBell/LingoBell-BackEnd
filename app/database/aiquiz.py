from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from app.database import Base

class AiQuiz(Base):
    __tablename__ = 'aiQuiz'

    aiQuizId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chatRoomId = Column(String(20), nullable=False)
    userId = Column(Integer, nullable=False) #개인화된 기록을 위함
    # chatRoomId = Column(String(20), ForeignKey('chatRooms.chatRoomId'), nullable=False)
    aiQuestion = Column(String(255), nullable=False)
    aiAnswer = Column(String(2), nullable=False)
    aiReason = Column(Text, nullable=False)
    aiQuizDate = Column(Date, nullable=False)
