import os
import logging
import telegram
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Review, Order
from .mistral import is_bad_review
from django.conf import settings
import requests

logger = logging.getLogger(__name__)

class TelegramNotifier:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.token = settings.TELEGRAM_BOT_API_KEY
        self.chat_id = settings.TELEGRAM_USER_ID
        self.session = requests.Session()
        
    def send(self, message):
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials not configured")
            return False
        
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Message sent to Telegram: {message[:100]}...")
            return True
        except Exception as e:
            logger.error(f"Telegram API error: {str(e)}")
            return False

# Глобальный экземпляр notifier
notifier = TelegramNotifier()

@receiver(post_save, sender=Review)
def handle_review_moderation(sender, instance, created, **kwargs):
    if not created:
        return
    
    try:
        instance.ai_checked_status = "ai_checked_in_progress"
        instance.save(update_fields=['ai_checked_status'])
        
        review_text = f"{instance.text} {instance.client_name or ''} {instance.master.name if instance.master else ''}"
        
        if is_bad_review(review_text):
            instance.ai_checked_status = "ai_cancelled"
            instance.is_published = False
            message = f"""⚠️ *Отзыв на модерации* #{instance.id}
👤 Клиент: {instance.client_name or 'Аноним'}
✂️ Мастер: {instance.master.name if instance.master else 'Не указан'}
⭐ Рейтинг: {'★' * instance.rating}
📝 Текст: {instance.text[:200]}{'...' if len(instance.text) > 200 else ''}
🚫 Причина: нарушение правил"""
        else:
            instance.ai_checked_status = "ai_checked_true"
            message = f"""✅ *Новый отзыв* #{instance.id}
👤 Клиент: {instance.client_name or 'Аноним'}
✂️ Мастер: {instance.master.name if instance.master else 'Не указан'}
⭐ Рейтинг: {'★' * instance.rating}
📝 Текст: {instance.text[:200]}{'...' if len(instance.text) > 200 else ''}"""
        
        if not notifier.send(message):
            logger.warning("Failed to send Telegram notification")
        
        instance.save(update_fields=['ai_checked_status', 'is_published'])
        
    except Exception as e:
        logger.error(f"Review processing error: {str(e)}")
        notifier.send(f"❌ Ошибка обработки отзыва #{instance.id}")

@receiver(m2m_changed, sender=Order.services.through)
def handle_new_order(sender, instance, action, pk_set, **kwargs):
    if action != "post_add" or not pk_set:
        return
    
    if timezone.now() - instance.created_at > timedelta(seconds=5):
        return
    
    try:
        services = "\n".join([f"• {s.name}" for s in instance.services.all()])
        total_price = sum(s.price for s in instance.services.all())
        
        message = f"""🆕 *Новый заказ* #{instance.id}
👤 Клиент: {instance.client_name}
📞 Телефон: `{instance.phone}`
✂️ Мастер: {instance.master.name if instance.master else 'Не выбран'}
📅 Дата: {instance.date.strftime('%d.%m.%Y %H:%M')}
💰 Сумма: {total_price} ₽
🔧 Услуги: {services}
💬 Комментарий: {instance.comment or 'Нет'}"""
        
        if not notifier.send(message):
            logger.warning("Failed to send order notification")
            
    except Exception as e:
        logger.error(f"Order processing error: {str(e)}")
        notifier.send(f"❌ Ошибка обработки заказа #{instance.id}")

@receiver(post_save, sender=Order)
def handle_order_update(sender, instance, created, **kwargs):
    if created or not instance.user:
        return
    
    try:
        status_map = {
            'new': '🆕 Создан',
            'confirmed': '✅ Подтвержден',
            'in_progress': '🛠 В работе',
            'completed': '✔️ Завершен',
            'cancelled': '❌ Отменен'
        }
        
        message = f"""ℹ️ *Обновление заказа* #{instance.id}
🔄 Статус: {status_map.get(instance.status, instance.status)}
✂️ Мастер: {instance.master.name if instance.master else 'Не указан'}
📅 Дата: {instance.date.strftime('%d.%m.%Y')}"""
        
        notifier.send(message)
        
    except Exception as e:
        logger.error(f"Order update error: {str(e)}")