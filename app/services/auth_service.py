from sqlalchemy.orm import Session
from app.database.models import User
from app.database import SessionLocal

def get_user_existance(db: Session, uid):
    user = db.query(User).filter(User.userCode == uid).first()
    print(user)
    if user is not None:
        return False
    else:
        return True