import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.api.dependencies import get_db
from app.db.database import Base
from app.db.models import Tariff

# Используем in-memory SQLite для мгновенных тестов
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


# Подменяем зависимость базы данных в FastAPI на тестовую
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    """Создает таблицы и базовые тарифы перед каждым тестом."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as db:
        db.add_all(
            [
                Tariff(id="basic", title="Basic", price=990000),
                Tariff(id="standard", title="Standard", price=1990000),
                Tariff(id="premium", title="Premium", price=2990000),
            ]
        )
        await db.commit()

    yield

    # Удаляем таблицы после теста, чтобы следующий был чистым
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client():
    """Асинхронный HTTP-клиент для тестирования эндпоинтов."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
