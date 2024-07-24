from sqlalchemy import Column, Integer, ForeignKey, String
from app.database import Base

class UserLearningLang(Base):
    __tablename__ = 'userLearningLangs'

    langCode = Column(String(500), ForeignKey('languages.langCode'), primary_key=True)
    userId = Column(Integer, ForeignKey('users.userCode'), primary_key=True)
    langLevel = Column(Integer, nullable=True)
