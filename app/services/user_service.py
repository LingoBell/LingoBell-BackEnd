from sqlalchemy.orm import Session
from app.database.models import User
from app.database import SessionLocal
from pydantic import BaseModel
from typing import Optional


class FormData(BaseModel):
        selectedInterests: List[str]
        gender : str
        name : str
        mainLanguage : str
        learningLanguages : List[str]
        languageWithLevel : List[str]
        userIntroduce: Optional[str] = None
        nation : str

def get_user_form_data(data : FormData):
    print("formData:", data)
    return data