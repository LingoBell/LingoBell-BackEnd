from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class ChatMessage(Base):
    __tablename__ = 'chatMessages'

    messageId = Column(Integer, primary_key=True, index=True)
    originalMessage = Column(String(500), nullable=False)
    chatRoomId = Column(Integer, ForeignKey('chatRooms.chatRoomId'), nullable=False)
    messageTime = Column(DateTime, nullable=False)
    translatedMessage = Column(String(500), nullable=True)
    messageSenderId = Column(Integer, ForeignKey('users.userCode'), nullable=False)
