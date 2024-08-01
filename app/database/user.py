from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    
    userId = Column(Integer, primary_key=True, autoincrement=True)
    userCode = Column(String(50), unique=True, index=True)
    userName = Column(String(255), unique=True, index=True)
    birthday = Column(Date)
    gender = Column(String(20))
    description = Column(String(255))
    nativeLanguage = Column(String(20))
    nation = Column(String(4))
    # nation = Column(String(4), ForeignKey('nation.nationId'))
    profileImages = Column(String(255), nullable=True)
