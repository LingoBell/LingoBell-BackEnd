from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base


#이 테이블은 뭔지 모르겠음 진우님에게 설명 요망!
class Notification(Base):
    __tablename__ = 'notifications'

    notificationId = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, nullable=False)
    # userId = Column(Integer, ForeignKey('users.userId'), nullable=False)
    notificationType = Column(String(500), nullable=False)
    notificationContents = Column(String(500), nullable=False)
    notificationTime = Column(DateTime, nullable=False)
