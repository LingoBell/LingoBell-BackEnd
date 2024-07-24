from sqlalchemy import Column, Integer, String, BLOB, ForeignKey, Boolean
from app.database import Base

class ChatRoom(Base):
    __tablename__ = 'chatRooms'

    chatRoomId = Column(Integer, primary_key=True, index=True)
    accessStatus = Column(Boolean, nullable=False)
    chatName = Column(String(500), nullable=False)
    chatRoomDescript = Column(String(500), nullable=True)
    chatContents = Column(BLOB, nullable=True)
    userId = Column(Integer, ForeignKey('users.userCode'), nullable=False)
    partnerId = Column(Integer, ForeignKey('users.userCode'), nullable=False) # 정희님, partnerId의 foreignKey 설정 확인해주세요.
