from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database.models import User
from app.database import SessionLocal

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

        user = db.query(User).filter(User.userCode == uid).first()
        
        return user_profile
    except Exception as e:
        db.rollback()
        print('ERROR')
        raise HTTPException(status_code=400, detail=str(e))
