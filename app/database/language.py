from sqlalchemy import Column, Integer, String
from app.database import Base

class Language(Base):
    __tablename__ = 'language'

    langId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    language = Column(String(20), nullable=False)
