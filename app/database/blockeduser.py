from sqlalchemy import Column, Integer, ForeignKey
from app.database import Base

class BlockedUser(Base):
    __tablename__ = 'blockedUsers'

    blockedUserId = Column(Integer, primary_key=True)
    userId = Column(Integer, primary_key=True)
    # blockedUserId = Column(Integer, ForeignKey('users.userId'), primary_key=True)
    # userId = Column(Integer, ForeignKey('users.userId'),primary_key=True)

