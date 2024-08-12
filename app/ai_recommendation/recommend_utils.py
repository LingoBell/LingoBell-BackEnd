import json
from deep_translator import GoogleTranslator
import google.generativeai as genai
from app.ai_recommendation.recommend_config import SYSTEM_PROMPT_TOPIC_RECOMMEND, SYSTEM_PROMPT_QUIZ_RECOMMEND
import logging
from dotenv import load_dotenv
import os

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini generative AI
api_key = os.getenv('GENAI_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-latest',
generation_config=genai.GenerationConfig(
temperature=0.9,
top_p=0.9,
response_mime_type="application/json"
))

# 출력언어 번역
def translate_text(text, target_lang):
    try:
        translation = GoogleTranslator(source='auto', target=target_lang).translate(text)
        logger.info(f"Translating '{text}' to '{target_lang}': '{translation}'")
        return translation
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text  # 번역 실패 시 원문 반환

# 주제추천 프롬프트 생성 함수
def generate_topic_prompt(user_input):
    user_prompt = f"""
    ### Conversation Content
    user_a: {user_input.user_a_content}
    user_b: {user_input.user_b_content}

    ### Interests
    user_a: {', '.join(user_input.user_a_interests)}
    user_b: {', '.join(user_input.user_b_interests)}

    ### User Languages
    user_a: {user_input.user_a_lang}
    user_b: {user_input.user_b_lang}

    ### Conversation Topic Recommendation
    - Recommend a conversation topic that user_a and user_b can talk about.
    - Provide 3 categories related to the topic, all of different types.
    - For each category, provide 2 sentence suggestions in the target language of user_b.
    - Output the conversation topic and categories in the language of user_a.
    - Ensure the sentence suggestions are in the target language of user_b.
    """
    return SYSTEM_PROMPT_TOPIC_RECOMMEND + user_prompt

# 번역 프롬프트 생성 함수
def generate_translation_prompt(text, target_lang):
    return f"Translate the following text to {target_lang}: {text}"

# 텍스트 번역 함수
def translate_text_via_prompt(text, target_lang):
    prompt = generate_translation_prompt(text, target_lang)
    response = model.generate_content(prompt)
    response_json = json.loads(response.text)
    translated_text = response_json.get("translation", "").strip()
    return translated_text



# 주제추천 형식 수정 함수
def format_recommendations(response_json, user_key, user_a_lang):
    recommendations = response_json.get(user_key, [])
    formatted_recommendations = []

    for recommendation in recommendations:
        topic = recommendation.get('topic', '')
        expressions = recommendation.get('expressions', [])

        # topic과 intro_text를 user_a_lang으로 번역
        translated_topic = translate_text_via_prompt(topic + "에 대해 이야기해 보세요!", user_a_lang)
        intro_text = translate_text_via_prompt('답변으로 추천하는 표현입니다.', user_a_lang)
        
        formatted_text = f"{translated_topic}\n{intro_text}"
        
        for i, expression in enumerate(expressions[:3], 1):  # 반드시 3개의 카테고리를 처리
            if 'category' in expression and 'expression' in expression:
                category = expression['category']
                exprs = expression['expression']
                formatted_text += f" {i}.{category}\n - {exprs[0]}\n - {exprs[1]}\n"
        
        formatted_recommendations.append(formatted_text)

    return formatted_recommendations

# 주제추천 함수
def get_topic_recommendations(user_input):
    prompt = generate_topic_prompt(user_input)
    logger.info(f"Generated prompt: {prompt}")
    
    response = model.generate_content(prompt)
    response_json = json.loads(response.text)
    logger.info(f"AI response: {response.text}")

    user_a_recommend = format_recommendations(response_json, 'user_a_recommend', user_input.user_a_lang)
    return {"user_a_recommend": user_a_recommend}


# 퀴즈 생성 프롬프트 함수
def generate_quiz_prompt(user_input):
    user_prompt = f"""
    ### 관심사
    user_a : {', '.join(user_input.user_a_interests)}

    ### 타겟언어
    user_b : {user_input.user_b_lang}

    ### 퀴즈를 생성해 주세요.
    """
    return SYSTEM_PROMPT_QUIZ_RECOMMEND + user_prompt


# 퀴즈 형식 수정 함수
def format_quizzes(response_json):
    quizzes = response_json.get('user_a_quiz', [])
    formatted_quizzes = []

    intro_text = "오늘의 퀴즈를 추천해드릴게요!"
    
    for quiz in quizzes:
        interest = quiz.get('interest', '')
        quiz_item = quiz.get('quiz', {})
        question = quiz_item.get('question', '')
        answer = quiz_item.get('answer', '')
        reason = quiz_item.get('reason', '')
        formatted_quiz = {
            "interest": interest,
            "quiz": {
                "question": question,
                "answer": answer,
                "reason": reason
            }
        }
        
        formatted_quizzes.append(formatted_quiz)

    return {"intro_text": intro_text, "user_a_quiz": formatted_quizzes}



# 퀴즈 생성 함수
def get_quiz_recommendations(user_input):
    prompt = generate_quiz_prompt(user_input)
    logger.info(f"Generated quiz prompt: {prompt}")
    
    response = model.generate_content(prompt)
    response_json = json.loads(response.text)
    logger.info(f"AI quiz response: {response.text}")

    # 형식 변환
    user_a_quiz = format_quizzes(response_json)
    return user_a_quiz




