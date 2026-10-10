import hmac
import hashlib
from fastapi import Request, HTTPException, Header, status
from app.core.config import settings


async def verify_signature(
    request: Request, x_signature: str | None = Header(None, alias="X-Signature")
):
    """Dependency для проверки HMAC-SHA256 подписи вебхука."""
    if not x_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature"
        )

    # Получаем сырое тело запроса в байтах
    body = await request.body()
    secret = settings.WEBHOOK_SECRET.encode("utf-8")

    # Генерируем ожидаемую подпись
    expected_signature = hmac.new(secret, body, hashlib.sha256).hexdigest()

    # Сравниваем безопасно (защита от timing attacks)
    if not hmac.compare_digest(expected_signature, x_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature"
        )  # Неверная подпись — 401
