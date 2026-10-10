from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator


class PaymentCreateRequest(BaseModel):
    tariff_id: str
    email: str
    method: Literal["card", "sbp", "installment"]  # Допустимые способы оплаты
    installment_months: Literal[3, 6, 12] | None = None  # Только 3, 6 или 12
    promo_code: str | None = None

    @field_validator("promo_code")
    @classmethod
    def validate_promo_code(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Регистр не важен, но неизвестный код должен вызвать ошибку[cite: 1]
        if v.upper() != "KVITTO10":
            raise ValueError("Invalid promo code")
        return v.upper()  # Нормализуем для удобства

    @model_validator(mode="after")
    def validate_installment(self) -> "PaymentCreateRequest":
        # Если рассрочка, параметр месяцев обязателен[cite: 1]
        if self.method == "installment" and self.installment_months is None:
            raise ValueError("installment_months is required for installment method")
        # Очищаем месяцы, если выбран другой метод
        if self.method != "installment":
            self.installment_months = None
        return self


# Схема для ответа API (совпадает с требованиями)[cite: 2]
class PaymentResponse(BaseModel):
    id: str
    status: str
    tariff_id: str
    amount: int
    discount: int
    method: str
    installment_months: int | None
    schedule: list[int] | None
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Схема для вебхука банка[cite: 2]
class WebhookRequest(BaseModel):
    payment_id: str
    status: str
