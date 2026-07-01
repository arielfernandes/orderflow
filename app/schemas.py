from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    amount_brl: float = Field(
        ..., gt=0, description='Amount in BRL to be converted.'
    )


class OrderResponse(BaseModel):
    id: int
    amount_brl: float
    status: str

    class config:
        from_attibure = True
