from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.database import Base

class User(Base):
    __tablename__ = 'users'

    userId = Column(Integer, primary_key=True, index=True)
    userName = Column(String(500), unique=True, index=True)
    email = Column(String(500), unique=True, index=True)
    pwd = Column(String(500))
    birth = Column(Date)
    sex = Column(String(500))
    description = Column(String(500))
    nation = Column(Integer, ForeignKey('nation.nationId'))
    profileImages = Column(String(500), nullable=True)
    userCode = Column(String(50), unique=True, index=True)