from sqlalchemy import Column, Integer, String, BLOB, ForeignKey, Boolean
from app.database import Base

class ChatRoom(Base):
    __tablename__ = 'chatRooms'

    chatRoomId = Column(Integer, primary_key=True, index=True)
    accessStatus = Column(Integer, nullable=False, default=1)
    chatName = Column(String(500), nullable=False)
    chatRoomDescript = Column(String(500), nullable=True)
    chatContents = Column(BLOB, nullable=True)
    userId = Column(Integer, ForeignKey('users.userCode'), nullable=False)
    partnerId = Column(Integer, ForeignKey('users.userCode'), nullable=False)
    joinStatus = Column(Integer, nullable=False, default=1)
