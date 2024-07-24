from sqlalchemy import Column, Integer, String
from app.database import Base

class Interest(Base):
    __tablename__ = 'interest'

    interCode = Column(Integer, primary_key=True, index=True)
    interName = Column(String(500), nullable=False)
