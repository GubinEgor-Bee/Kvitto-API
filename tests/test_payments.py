import pytest
import hmac
import hashlib
import json
from app.core.config import settings

pytestmark = pytest.mark.asyncio


# 1. Сумма с промокодом и без, в том числе в нижнем регистре[cite: 2]
async def test_create_payment_with_and_without_promo(async_client):
    # Без промокода
    resp1 = await async_client.post(
        "/payments",
        json={"tariff_id": "standard", "email": "test@test.ru", "method": "card"},
    )
    assert resp1.status_code == 201
    assert resp1.json()["amount"] == 1990000

    # С промокодом kvitto10 (нижний регистр)
    resp2 = await async_client.post(
        "/payments",
        json={
            "tariff_id": "standard",
            "email": "test@test.ru",
            "method": "card",
            "promo_code": "kvitto10",
        },
    )
    assert resp2.status_code == 201
    # 1990000 - 10% = 1791000
    assert resp2.json()["amount"] == 1791000


# 2. График рассрочки: сумма графика равна сумме к оплате для 3, 6 и 12 месяцев[cite: 2]
@pytest.mark.parametrize("months", [3, 6, 12])
async def test_installment_schedule_sums(async_client, months):
    resp = await async_client.post(
        "/payments",
        json={
            "tariff_id": "standard",
            "email": "test@test.ru",
            "method": "installment",
            "installment_months": months,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    # Проверяем, что сумма элементов массива равна итоговой стоимости
    assert sum(data["schedule"]) == data["amount"]
    assert len(data["schedule"]) == months


# 3. Повторный запрос с тем же Idempotency-Key не создает второй платеж[cite: 2]
async def test_idempotency_key_prevents_duplicates(async_client):
    payload = {"tariff_id": "basic", "email": "dup@test.ru", "method": "card"}
    headers = {"Idempotency-Key": "unique-key-123"}

    # Первый запрос
    resp1 = await async_client.post("/payments", json=payload, headers=headers)
    assert resp1.status_code == 201
    payment_id_1 = resp1.json()["id"]

    # Второй запрос с тем же ключом
    resp2 = await async_client.post("/payments", json=payload, headers=headers)
    assert resp2.status_code == 200  # Возвращается 200, а не 201[cite: 2]
    assert resp2.json()["id"] == payment_id_1  # ID совпадает с первым платежом


# 4. Запрещенный переход статуса возвращает 409 и не меняет статус[cite: 2]
async def test_invalid_status_transition(async_client):
    # Создаем платеж (по умолчанию статус pending)
    resp = await async_client.post(
        "/payments",
        json={"tariff_id": "basic", "email": "status@test.ru", "method": "card"},
    )
    payment_id = resp.json()["id"]

    # Пытаемся перевести pending -> refunded (запрещено матрицей переходов)[cite: 1]
    body = {"payment_id": payment_id, "status": "refunded"}

    # Жестко сериализуем без пробелов, чтобы гарантировать совпадение байтов
    body_bytes = json.dumps(body, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(
        settings.WEBHOOK_SECRET.encode("utf-8"), body_bytes, hashlib.sha256
    ).hexdigest()

    # ВАЖНО: передаем content=body_bytes, а не json=body!
    webhook_resp = await async_client.post(
        "/webhooks/bank",
        content=body_bytes,
        headers={"X-Signature": signature, "Content-Type": "application/json"},
    )
    assert webhook_resp.status_code == 409
    assert webhook_resp.json() == {"error": "invalid_transition"}

    # Проверяем базу, что статус реально не изменился
    get_resp = await async_client.get(f"/payments/{payment_id}")
    assert get_resp.json()["status"] == "pending"


# 5. Запрос несуществующего платежа возвращает 404[cite: 2]
async def test_get_nonexistent_payment_returns_404(async_client):
    resp = await async_client.get("/payments/non-existent-uuid-1234")
    assert resp.status_code == 404
