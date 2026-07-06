import uuid

from src.config import logger
from src.domain.enums import PaymentStatus
from src.domain.models import Outbox, Payment
from src.schemas.payments import OUTBOX_EVENT_TYPE, PaymentCreateRequest
from src.services.uow import Uow


async def add_payment(
    uow: Uow,
    request: PaymentCreateRequest,
    idempotency_key: str,
) -> Payment:
    async with uow:
        existing_payment = await uow.payments.get_by_idempotency_key(
            idempotency_key,
        )

        if existing_payment is not None:
            logger.info('Payment with idempotency_key %s already exists', idempotency_key)
            return existing_payment

        payment = Payment(
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            meta=request.metadata,
            webhook_url=str(request.webhook_url),
            idempotency_key=idempotency_key,
            status=PaymentStatus.PENDING,
        )
        uow.payments.add(payment)
        await uow.session.flush()

        outbox = Outbox(
            event_type=OUTBOX_EVENT_TYPE,
            payload={
                'payment_id': str(payment.id),
            },
        )
        uow.outbox.add(outbox)

        await uow.commit()
        await uow.refresh(payment)

        logger.info('Payment with idempotency_key %s successfully created', idempotency_key)

        return payment


async def get_payment(uow: Uow, payment_id: uuid.UUID) -> Payment:
    async with uow:
        db_item = await uow.payments.get_or_error(payment_id)
        return db_item
