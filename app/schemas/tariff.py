from pydantic import BaseModel


class TariffResponse(BaseModel):
    id: str
    title: str
    price: int

    model_config = {"from_attributes": True}
