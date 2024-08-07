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
    ### 대화내용
    user_a: {user_input.user_a_content}
    user_b: {user_input.user_b_content}

    ### 관심사
    user_a : {', '.join(user_input.user_a_interests)}
    user_b : {', '.join(user_input.user_b_interests)}

    ### 사용자언어
    user_a : {user_input.user_a_lang}
    user_b : {user_input.user_b_lang}

    ### 대화 주제를 추천해 주세요.
    """
    return SYSTEM_PROMPT_TOPIC_RECOMMEND + user_prompt

# 주제추천 형식 수정 함수
def format_recommendations(response_json, user_key, user_a_lang, user_b_lang):
    recommendations = response_json.get(user_key, [])
    formatted_recommendations = []

    for recommendation in recommendations:
        # 주제는 user_a의 언어로 출력
        topic = translate_text(f"{recommendation.get('topic', '')}에 대해 이야기해 보세요!", user_a_lang)
        expressions = recommendation.get('expressions', [])

        # '답변으로 추천하는 표현입니다.' 부분도 user_a의 언어로 출력
        intro_text = translate_text('답변으로 추천하는 표현입니다.', user_a_lang)
        formatted_text = f"{topic}\n{intro_text}\n"
        
        for i, expression in enumerate(expressions[:3], 1):  # 반드시 3개의 카테고리를 처리
            if 'category' in expression and 'expression' in expression:
                # 카테고리도 user_a의 언어로 출력
                category = translate_text(expression['category'], user_a_lang)
                # 표현은 리스트로 감싸서 2개의 문장추천을 포함
                exprs = [translate_text(expr, user_b_lang) for expr in expression['expression']]
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

    # 형식 변환
    user_a_recommend = format_recommendations(response_json, 'user_a_recommend', user_input.user_a_lang, user_input.user_b_lang)
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
def format_quizzes(response_json, user_a_lang, user_b_lang):
    quizzes = response_json.get('user_a_quiz', [])
    formatted_quizzes = []

    intro_text = translate_text("오늘의 퀴즈를 추천해드릴게요!", user_a_lang)
    
    for quiz in quizzes:
        interest = translate_text(quiz.get('interest', ''), user_a_lang)
        quiz_item = quiz.get('quiz', {})
        question = translate_text(quiz_item.get('question', ''), user_b_lang)
        answer = quiz_item.get('answer', '')
        reason = translate_text(quiz_item.get('reason', ''), user_b_lang)
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
    user_a_quiz = format_quizzes(response_json, user_input.user_a_lang, user_input.user_b_lang)
    return user_a_quiz


