from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.dependencies import get_db
from app.db.models import Tariff
from app.schemas.tariff import TariffResponse

router = APIRouter(prefix="/tariffs", tags=["Tariffs"])


@router.get("", response_model=list[TariffResponse])
async def get_tariffs(db: AsyncSession = Depends(get_db)):
    """Получить список всех тарифов."""
    result = await db.execute(select(Tariff))
    return result.scalars().all()
