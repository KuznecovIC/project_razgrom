# signals.py (новый файл в вашем приложении)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Review
from .mistral import is_bad_review
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Review)
def moderate_review(sender, instance, created, **kwargs):
    """
    Сигнал для автоматической модерации отзывов при их создании
    """
    if created:
        try:
            instance.ai_checked_status = "ai_checked_in_progress"
            instance.save(update_fields=['ai_checked_status'])
            
            review_text = f"{instance.text} {instance.client_name} {instance.master.name}"
            
            if is_bad_review(review_text):
                instance.ai_checked_status = "ai_cancelled"
                instance.is_published = False
                logger.warning(f"Отзыв {instance.id} помечен как недопустимый")
            else:
                instance.ai_checked_status = "ai_checked_true"
                logger.info(f"Отзыв {instance.id} прошел модерацию")
            
            instance.save(update_fields=['ai_checked_status', 'is_published'])
            
        except Exception as e:
            instance.ai_checked_status = "ai_check_failed"
            instance.save(update_fields=['ai_checked_status'])
            logger.error(f"Ошибка модерации отзыва {instance.id}: {str(e)}")