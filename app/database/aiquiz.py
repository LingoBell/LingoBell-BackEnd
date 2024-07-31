from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.database import Base

class AiQuiz(Base):
    __tablename__ = 'aiQuiz'

    aiQuizId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chatRoomId = Column(Integer, nullable=False)
    # chatRoomId = Column(Integer, ForeignKey('chatRooms.chatRoomId'), nullable=False)
    aiQuestion = Column(String(255), nullable=False)
    aiAnswer = Column(String(2), nullable=False)
    aiReason = Column(String(255), nullable=False)
    aiQuizDate = Column(Date, nullable=False)
