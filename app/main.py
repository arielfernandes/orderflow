import json

import models
import pika
import schemas
from database import engine, get_db
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title='Orderflow Foreign Exchange PoC')

RABBITMQ_URL = 'amqp://guest:guest@localhost:5672/'


def publish_to_rabbitmq(queue_name: str, message: dict):
    parameters = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=queue_name, durable=True)

    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent
        ),
    )
    connection.close()


@app.post(
    '/orders/',
    response_model=schemas.OrderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    db_order = models.Order(amount_brl=order.amount_brl, status='PENDING')
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    payload = {'order_id': db_order.id, 'amount_brl': db_order.amount_brl}

    try:
        publish_to_rabbitmq(queue_name='conversion_queue', message=payload)
    except pika.exceptions.AMQPConnectionError:
        db.rollback()

        db_order.status = 'FAILED'
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Processing queue is unavailable.',
        )
    return db_order
