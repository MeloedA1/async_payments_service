import uuid

import httpx
from faststream.rabbit import RabbitQueue
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from src.config import logger
from src.entrypoints.dependencies.rabbit import broker
from src.entrypoints.dependencies.uow import get_uow
from src.services.payment_processing import PaymentProcessingService

payments_dlq = RabbitQueue(
    'payments.dlq',
    durable=True,
)

payments_queue = RabbitQueue(
    'payments.new',
    durable=True,
    arguments={
        'x-dead-letter-exchange': '',
        'x-dead-letter-routing-key': 'payments.dlq',
    },
)


class PaymentCreatedEvent(BaseModel):
    payment_id: uuid.UUID


@broker.subscriber(payments_queue)
async def handle_payment_created(message: dict) -> None:

    event = PaymentCreatedEvent.model_validate(message)

    service = PaymentProcessingService(
        uow=get_uow(),
    )

    try:
        await service.process(event.payment_id)
    except SQLAlchemyError:
        logger.exception('Database error while processing payment %s', event.payment_id)
        raise
    except httpx.HTTPError:
        logger.exception('Webhook delivery failed for payment %s', event.payment_id)
        raise
