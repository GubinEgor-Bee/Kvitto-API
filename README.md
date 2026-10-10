```markdown
# Kvitto Payments API

Сервис для приема оплат онлайн-школы через платформу Квитто. Реализован на FastAPI с использованием асинхронной архитектуры и строгой типизации сумм (только целые копейки).

## Реализованные фичи и бонусы
- **Расчет рассрочки без потерь**: алгоритм честного распределения остатка от деления копеек[cite: 1, 3].
- **Идемпотентность**: защита от двойных списаний через заголовок `Idempotency-Key`[cite: 2, 3].
- **Защита вебхуков**: верификация статусов от банка по `X-Signature` (HMAC-SHA256)[cite: 4].
- **Стейт-машина статусов**: строгий контроль бизнес-правил переходов статусов платежа[cite: 1, 3].
- **Бонусы**: Docker Compose, миграции Alembic, CI-пайплайн (GitHub Actions) с `ruff` и `pytest`, расширенная фильтрация (`GET /payments?email=...&status=...`), правила для ИИ-ассистентов (`.cursorrules`)[cite: 4].

## Стек технологий
- Python 3.11+ / FastAPI / Pydantic v2[cite: 1]
- PostgreSQL / SQLAlchemy 2.0 (asyncpg) / Alembic[cite: 1, 4]
- Pytest (с in-memory SQLite для мгновенных тестов)[cite: 1]
- Docker / Docker Compose[cite: 4]

---

## 🚀 Запуск проекта

### Вариант 1: Через Docker Compose (Рекомендуемый)
```bash
docker compose up --build

```

API будет доступно по адресу: http://127.0.0.1:8000/docs

### Вариант 2: Локальный запуск

1. Установите зависимости:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

2. Настройте `.env` файл в корне проекта:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:15432/kvitto
WEBHOOK_SECRET=super_secret_key_123

```

3. Примените миграции (база данных уже должна быть создана):

```bash
alembic upgrade head

```

4. Запустите сервер:

```bash
uvicorn app.main:app --reload

```

---

## 🧪 Тестирование

Проект покрыт автотестами (проверяются правила переходов статусов, расчет рассрочки, идемпотентность и криптографическая подпись)[cite: 2]. Тесты используют изолированную in-memory SQLite базу.

```bash
pip install aiosqlite
pytest -v

```

---

## 📡 Примеры использования (cURL)

**1. Получить список тарифов**

```bash
curl -X 'GET' '[http://127.0.0.1:8000/tariffs](http://127.0.0.1:8000/tariffs)' -H 'accept: application/json'

```

**2. Создать платеж (рассрочка на 3 месяца с промокодом)**

```bash
curl -X 'POST' \
  '[http://127.0.0.1:8000/payments](http://127.0.0.1:8000/payments)' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: my-unique-key-123' \
  -d '{
  "tariff_id": "standard",
  "email": "student@test.ru",
  "method": "installment",
  "installment_months": 3,
  "promo_code": "KVITTO10"
}'

```

**3. Уведомление от банка (смена статуса на succeeded)**
*Замените `<СГЕНЕРИРОВАННАЯ_ПОДПИСЬ>` на реальный HMAC-SHA256 хеш от тела запроса.*

```bash
curl -X 'POST' \
  '[http://127.0.0.1:8000/webhooks/bank](http://127.0.0.1:8000/webhooks/bank)' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'X-Signature: <СГЕНЕРИРОВАННАЯ_ПОДПИСЬ>' \
  -d '{
  "payment_id": "<ID_ПЛАТЕЖА>",
  "status": "succeeded"
}'

```

```

```