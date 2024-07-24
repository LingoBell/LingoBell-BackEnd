from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class AIMessage(Base):
    __tablename__ = 'aiMessages'

    aiMessageId = Column(Integer, primary_key=True, index=True)
    chatRoomId = Column(Integer, ForeignKey('chatRooms.chatRoomId'), nullable=False)
    aiMessageType = Column(String(500), nullable=False)
    aiMessageContents = Column(String(500), nullable=False)
    aiMessageTime = Column(DateTime, nullable=False)
