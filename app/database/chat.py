from sqlalchemy import Column, Integer, String, BLOB, ForeignKey, Boolean
from app.database import Base

class ChatRoom(Base):
    __tablename__ = 'chatRooms'

    chatRoomId = Column(String(20), primary_key=True)
    accessStatus = Column(Integer, nullable=False, default=1) #접근여부 -> 1:기본값, 2: 접근불가
    userId = Column(Integer, nullable=False)
    partnerId = Column(Integer, nullable=False)
    # userId = Column(Integer, ForeignKey('users.userId'), nullable=False)
    # partnerId = Column(Integer, ForeignKey('users.userId'), nullable=False)
    joinStatus = Column(Integer, nullable=False, default=1) #수락여부 -> 1: 기본값, 2: 수락한 상태
    userDeleteStatus = Column(Integer, default=0) #삭제여부 -> 0:기본값, 1:삭제
    partnerDeleteStatus = Column(Integer, default=0) #삭제여부 -> 0:기본값, 1:삭제
