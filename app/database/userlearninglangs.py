from sqlalchemy import Column, Integer, ForeignKey, String
from app.database import Base

class UserLearningLang(Base):
    __tablename__ = 'userLearningLangs'

    # langId = Column(Integer, ForeignKey('language.langId'), primary_key=True)
    # userId = Column(Integer, ForeignKey('users.userId'), primary_key=True)
    langId = Column(Integer, primary_key=True)
    userId = Column(Integer, primary_key=True)
    langLevel = Column(Integer, nullable=True)
