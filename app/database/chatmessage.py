from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

# STT - TTS 기반 스크립트 테이블
class ChatMessage(Base):
    __tablename__ = 'chatMessages'

    messageId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chatRoomId = Column(Integer, primary_key=True, nullable=False)
    # chatRoomId = Column(Integer, ForeignKey('chatRooms.chatRoomId'), primary_key=True, nullable=False)
    originalMessage = Column(String(500), nullable=False)
    translatedMessage = Column(String(500), nullable=True)
    messageTime = Column(DateTime, nullable=False)
    messageSenderId = Column(Integer, nullable=False)
    # messageSenderId = Column(Integer, ForeignKey('users.userId'), nullable=False)
