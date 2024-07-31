from sqlalchemy import Column, Integer, Date, ForeignKey
from app.database import Base

class AttendUser(Base):
    __tablename__ = 'attendUsers'

    attendDate = Column(Date, primary_key=True)
    userId = Column(Integer, primary_key=True)
    # userId = Column(Integer, ForeignKey('users.userId'), primary_key=True)
