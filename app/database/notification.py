from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class Notification(Base):
    __tablename__ = 'notifications'

    notificationId = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey('users.userCode'), nullable=False)
    notificationType = Column(String(500), nullable=False)
    notificationContents = Column(String(500), nullable=False)
    notificationTime = Column(DateTime, nullable=False)
