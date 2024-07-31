from sqlalchemy import Column, Integer, String
from app.database import Base

class Interest(Base):
    __tablename__ = 'interest'

    interestId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interestName = Column(String(20), nullable=False)
