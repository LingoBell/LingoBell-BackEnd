from sqlalchemy import Column, Integer, ForeignKey
from app.database import Base

class BlockedUser(Base):
    __tablename__ = 'blockedUsers'

    blockedUserId = Column(Integer, ForeignKey('users.userCode'), primary_key=True)
    userId = Column(Integer, ForeignKey('users.userCode'), nullable=False)
