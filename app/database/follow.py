from sqlalchemy import Column, Integer, ForeignKey
from app.database import Base

class Follow(Base):
    __tablename__ = 'follows'

    followUserId = Column(Integer, primary_key=True)
    userId = Column(Integer, primary_key=True, nullable=False)
    # followUserId = Column(Integer, ForeignKey('users.userId'), primary_key=True)
    # userId = Column(Integer, ForeignKey('users.userId'), primary_key=True, nullable=False)
    followStatus = Column(Integer, nullable=False, default=1) #친구 요청 상태 ->  1:기본값, 2:요청된 상태, 3: 수락