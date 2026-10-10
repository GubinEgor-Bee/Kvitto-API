from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.security import verify_signature
from app.db.models import Payment
from app.schemas.payment import WebhookRequest
from app.services.payment_srv import InvalidTransitionError, PaymentService

# Подключаем зависимость verify_signature ко всему роутеру
router = APIRouter(
    prefix="/webhooks", tags=["Webhooks"], dependencies=[Depends(verify_signature)]
)


@router.post("/bank")
async def bank_webhook(
    webhook_data: WebhookRequest, db: AsyncSession = Depends(get_db)
):
    """Эндпоинт для приема уведомлений от банка."""
    # 1. Проверяем существование платежа
    payment = await db.get(Payment, webhook_data.payment_id)
    if not payment:
        raise HTTPException(
            status_code=404, detail="Payment not found"
        )  # Платежа нет - 404

    # 2. Проверяем бизнес-правило перехода статуса
    try:
        PaymentService.check_status_transition(payment.status, webhook_data.status)
    except InvalidTransitionError:
        # Запрещенный переход - 409
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "invalid_transition"},
        )

    # 3. Обновляем статус, если всё ок
    payment.status = webhook_data.status
    await db.commit()

    # Успех - 200 { result: "ok" }
    return {"result": "ok"}
