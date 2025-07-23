# mistral.py
#from barbershop.settings import MISTRAL_MODERATION_GRADES
import os
from dotenv import load_dotenv
from mistralai import Mistral
from pprint import pprint
import logging

load_dotenv()

logger = logging.getLogger(__name__)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODERATION_GRADES = {
    "hate_and_discrimination": 0.1,
    "sexual": 0.1,
    "violence_and_threats": 0.1,
    "dangerous_and_criminal_content": 0.1,
    "selfharm": 0.1,
    "health": 0.1,
    "financial": 0.1,
    "law": 0.1,
    "pii": 0.1
}

def is_bad_review(review_text: str, api_key: str = MISTRAL_API_KEY, grades: dict = MISTRAL_MODERATION_GRADES) -> bool:
    """
    Проверяет отзыв на наличие недопустимого контента с помощью Mistral AI
    
    Args:
        review_text: Текст отзыва для проверки
        api_key: API ключ Mistral
        grades: Пороговые значения для категорий модерации
        
    Returns:
        bool: True если отзыв содержит недопустимый контент
    """
    if not review_text.strip():
        return False
        
    try:
        client = Mistral(api_key=api_key)
        
        # Добавляем контекст для лучшего определения оскорблений
        full_text = f"""
        Это отзыв о парикмахерской. Определи, содержит ли текст оскорбления, 
        ненормативную лексику или другие нарушения. Текст отзыва: {review_text}
        """
        
        response = client.classifiers.moderate_chat(
            model="mistral-moderation-latest",
            inputs=[{"role": "user", "content": full_text}],
        )

        if not response.results:
            return False
            
        result = response.results[0].category_scores
        result = {key: round(value, 2) for key, value in result.items()}

        logger.debug(f"Результаты модерации: {result}")
        pprint(result)

        # Проверяем только нужные категории
        checked_categories = {
            'hate_and_discrimination': result.get('hate_and_discrimination', 0),
            'sexual': result.get('sexual', 0),
            'violence_and_threats': result.get('violence_and_threats', 0),
            'dangerous_and_criminal_content': result.get('dangerous_and_criminal_content', 0)
        }

        for category, score in checked_categories.items():
            if score >= grades.get(category, 0.1):
                logger.warning(f"Обнаружено нарушение: {category} (score: {score})")
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Ошибка при модерации отзыва: {str(e)}")
        return False


if __name__ == "__main__":
    # Тестовые случаи
    test_cases = [
        ("Отличный мастер, всем рекомендую!", False),
        ("Пидор тупой, испортил стрижку!", True),
        ("Дядя Толик - лучший парикмахер!", False),
        ("Стрижка отстой, никогда больше не приду!", False),
        ("Этот парикмахер - полный дебил!", True)
    ]
    
    for text, expected in test_cases:
        print(f"\nТестируем: '{text}'")
        result = is_bad_review(text)
        print(f"Ожидаем: {expected}, Получили: {result}")
        print("="*50)