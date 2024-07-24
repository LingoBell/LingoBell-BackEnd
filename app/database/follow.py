from sqlalchemy import Column, Integer, Boolean, ForeignKey
from app.database import Base

class Follow(Base):
    __tablename__ = 'follows'

    followUserId = Column(Integer, ForeignKey('users.userCode'), primary_key=True)
    userId = Column(Integer, ForeignKey('users.userCode'), nullable=False)
    followStatus = Column(Boolean, nullable=False)
