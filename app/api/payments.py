
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.db.models import Payment, Tariff
from app.schemas.payment import PaymentCreateRequest, PaymentResponse
from app.services.payment_srv import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse)
async def create_payment(
    request: PaymentCreateRequest,
    response: Response,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    # 1. Защита от дублей: если ключ передан и такой платеж уже есть, возвращаем его с кодом 200[cite: 2]
    if idempotency_key:
        stmt = select(Payment).where(Payment.idempotency_key == idempotency_key)
        result = await db.execute(stmt)
        existing_payment = result.scalar_one_or_none()
        if existing_payment:
            response.status_code = status.HTTP_200_OK
            return existing_payment

    # 2. Проверка существования тарифа
    tariff = await db.get(Tariff, request.tariff_id)
    if not tariff:
        raise HTTPException(status_code=404, detail="Tariff not found")

    # 3. Расчет бизнес-логики (скидки и копейки)
    amount, discount = PaymentService.calculate_discount_and_amount(
        tariff.price, request.promo_code
    )

    schedule = None
    if request.method == "installment":
        schedule = PaymentService.calculate_schedule(amount, request.installment_months)

    # 4. Сохранение в БД
    new_payment = Payment(
        tariff_id=request.tariff_id,
        amount=amount,
        discount=discount,
        method=request.method,
        installment_months=request.installment_months,
        schedule=schedule,
        email=request.email,
        idempotency_key=idempotency_key,
    )
    db.add(new_payment)
    await db.commit()
    await db.refresh(new_payment)

    # Успешное создание — код 201[cite: 2]
    response.status_code = status.HTTP_201_CREATED
    return new_payment


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    """Получить платеж по ID."""
    payment = await db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(
            status_code=404, detail="Payment not found"
        )  # Ошибка 404, если нет платежа[cite: 2]
    return payment


# БОНУС: GET /payments с фильтрами по email и status[cite: 4]
@router.get("", response_model=list[PaymentResponse])
async def list_payments(
    email: str | None = Query(None),
    payment_status: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Payment)
    if email:
        stmt = stmt.where(Payment.email == email)
    if payment_status:
        stmt = stmt.where(Payment.status == payment_status)

    result = await db.execute(stmt)
    return result.scalars().all()
