from pydantic import BaseModel

class UserTopicInput(BaseModel):
    user_a_content : str
    user_b_content : str
    user_a_interests : list[str]
    user_b_interests : list[str]
    user_a_lang : str
    user_b_lang : str

class UserQuizInput(BaseModel):
    user_b_lang : str
    user_a_lang : str
    user_a_interests : list[str]

