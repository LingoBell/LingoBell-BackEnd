from sqlalchemy import Column, Integer, ForeignKey
from app.database import Base

class UserInterest(Base):
    __tablename__ = 'userInterests'

    interCode = Column(Integer, ForeignKey('interest.interCode'))
    userId = Column(Integer, ForeignKey('users.userId'), primary_key=True) # 정희님, 회원관심사 테이블의 USER_CODE를 userId로 변경했어요. 다른 테이블과 통일하기 위해. 그리고 PK값이 없어서 userId에 달아놨어요.
