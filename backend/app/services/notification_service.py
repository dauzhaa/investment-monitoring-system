import logging
from email.message import EmailMessage
import aiosmtplib
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_real_email(email_to: str, subject: str, body: str):
    """
    Асинхронная отправка реального Email сообщения.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("⚠️ SMTP не настроен. Письмо не отправлено.")
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_USER
    message["To"] = email_to
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=settings.SMTP_USE_TLS,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
        )
        logger.info(f"✅ Email успешно отправлен на {email_to}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки email на {email_to}: {e}")