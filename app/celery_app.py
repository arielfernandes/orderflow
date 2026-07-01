import time

from celery import Celery
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Order

celery_app = Celery(
    'orderflow',
    broker='amqp://guest:guest@localhost:5672//',
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, name='process_conversion', max_retries=3)
def process_conversion(self, order_id: int, amount_brl: float):
    db: Session = SessionLocal()
    order = None
    try:  # noqa
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status != 'PENDING':
            return {'error': 'Invalid state or order not found'}

        order.status = 'PROCESSING'
        db.commit()

        time.sleep(2)
        exchange_rate = 0.20
        amount_usd = amount_brl * exchange_rate

        order.amount_usd = amount_usd
        order.status = 'COMPLETED'
        db.commit()

        return {'order_id': order_id, 'usd': amount_usd, 'status': 'COMPLETED'}

    except Exception as exc:
        db.rollback()
        if self.request.retries == self.max_retries and order:
            order.status = 'FAILED'
            db.commit()

        raise self.retry(exc=exc, countdown=2**self.request.retries)
    finally:
        db.close()
