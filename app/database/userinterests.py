from sqlalchemy import Column, Integer, ForeignKey
from app.database import Base

class UserInterest(Base):
    __tablename__ = 'userInterests'

    userId = Column(Integer, primary_key=True)
    interestId = Column(Integer, primary_key=True)
    # interCode = Column(Integer, ForeignKey('interest.interestId'))
    # userId = Column(Integer, ForeignKey('users.userId'), primary_key=True)