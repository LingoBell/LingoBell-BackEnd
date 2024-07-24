from sqlalchemy import Column, Integer, Date, Time, ForeignKey
from app.database import Base

class UserSchedule(Base):
    __tablename__ = 'userSchedules'

    scheduleId = Column(Integer, primary_key=True, index=True)
    scheduleDate = Column(Date, nullable=False)
    chatStartTime = Column(Time, nullable=False)
    chatEndTime = Column(Time, nullable=False)
    userId = Column(Integer, ForeignKey('users.userCode'), nullable=False)
    partnerId = Column(Integer, ForeignKey('users.userCode'), nullable=False) # 정희님 foreignKey 확인해주세요.
