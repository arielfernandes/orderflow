from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.celery_app import process_conversion
from app.database import engine, get_db
from app.models import Base, Order
from app.schemas import OrderCreate, OrderResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title='Orderflow Foreign Exchange PoC')


@app.post(
    '/orders/',
    response_model=OrderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = Order(amount_brl=order.amount_brl, status='PENDING')
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    try:
        process_conversion.apply_async(
            args=[db_order.id, db_order.amount_brl], queue='celery'
        )
    except Exception:
        db_order.status = 'FAILED'
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Broker is unavailable.',
        )
    return db_order
