from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database.models import User
from app.database import SessionLocal

#유저 존재 유무 판별
def get_user_existance(db: Session, uid):
    user = db.query(User).filter(User.userCode == uid).first()
    print(user)
    if user is not None:
        return False
    else:
        return True

def add_user_profile_data(db : Session, uid : str, form_data : dict):    
    try:
        user_profile = User(
            userCode=uid,
            userName=form_data['name'],
            gender=form_data['gender'],
            description=form_data['userIntroduce'],
            # nation=form_data.get('nation', {}).get('label'),
            # mainLanguage=form_data['mainLanguage']
        )
        db.add(user_profile)
        db.commit()
        db.refresh(user_profile)
        print('success db')
        user = db.query(User).filter(User.userCode == uid).first()
        print('user!!:',user)
        return user_profile
    except Exception as e:
        db.rollback()
        print('ERROR')
        raise HTTPException(status_code=400, detail=str(e))
