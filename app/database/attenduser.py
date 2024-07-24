from sqlalchemy import Column, Integer, Date, ForeignKey
from app.database import Base

class AttendUser(Base):
    __tablename__ = 'attendUsers'

    attendDate = Column(Date, nullable=False)
    userId = Column(Integer, ForeignKey('users.userCode'), primary_key=True)
