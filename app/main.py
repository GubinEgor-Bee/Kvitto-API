from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import select
from app.db.database import async_session_maker
from app.db.models import Tariff

# Импортируем наши роутеры
from app.api.webhooks import router as webhooks_router
from app.api.tariffs import router as tariffs_router
from app.api.payments import router as payments_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Выполняется при старте приложения
    async with async_session_maker() as db:
        # Проверяем, есть ли уже тарифы в базе
        result = await db.execute(select(Tariff).where(Tariff.id == "basic"))
        if not result.scalar_one_or_none():
            # Создаются при старте: basic 9900, standard 19900, premium 29900 (в копейках)[cite: 1]
            db.add_all(
                [
                    Tariff(id="basic", title="Basic", price=990000),
                    Tariff(id="standard", title="Standard", price=1990000),
                    Tariff(id="premium", title="Premium", price=2990000),
                ]
            )
            await db.commit()
    yield
    # Здесь можно добавить логику при выключении приложения, если нужно


app = FastAPI(
    title="Kvitto API", description="API платежей для онлайн-школы", lifespan=lifespan
)

app.include_router(tariffs_router)
app.include_router(payments_router)
app.include_router(webhooks_router)
