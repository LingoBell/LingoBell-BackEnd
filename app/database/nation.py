from sqlalchemy import Column, Integer, String
from app.database import Base

class Nation(Base):
    __tablename__ = 'nation'

    nationId = Column(Integer, primary_key=True, index=True)
    nationName = Column(String(500), nullable=False)
