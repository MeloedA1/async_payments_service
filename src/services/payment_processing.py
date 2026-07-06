import asyncio
import logging
import random
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from tenacity import before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.config import logger
from src.domain.enums import PaymentStatus
from src.entrypoints.dependencies.uow import Uow


class WebhookPayload(BaseModel):
    payment_id: uuid.UUID
    status: PaymentStatus
    amount: Decimal
    currency: str
    processed_at: datetime


class PaymentProcessingService:
    def __init__(
        self,
        uow: Uow,
    ):
        self.uow = uow

    async def process(self, payment_id: uuid.UUID) -> None:
        async with self.uow as uow:
            payment = await uow.payments.get_by_id(payment_id)

            if payment is None:
                raise ValueError(f"Payment {payment_id} not found")

            status = await self._emulate_payment_gateway()

            try:
                payment.status = status
                payment.processed_at = datetime.now(UTC)

                await uow.commit()
                await uow.refresh(payment)

            except SQLAlchemyError:
                await uow.rollback()
                logger.exception('Failed to update payment %s', payment.id)
                raise

            logger.info('Payment with payment_id %s processed', payment_id)

            webhook_payload = WebhookPayload(
                payment_id=payment.id,
                status=payment.status,
                amount=payment.amount,
                currency=payment.currency.value,
                processed_at=payment.processed_at,
            )

        await self._send_webhook_with_retry(
            webhook_url=payment.webhook_url,
            payload=webhook_payload.model_dump(mode='json'),
        )
        logger.info('Webhook for payment_id %s sent', payment_id)

    async def _emulate_payment_gateway(self) -> PaymentStatus:
        await asyncio.sleep(random.randint(2, 5))

        if random.random() < 0.9:
            return PaymentStatus.SUCCEEDED

        return PaymentStatus.FAILED

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(httpx.HTTPError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _send_webhook_with_retry(self, webhook_url: str, payload: dict[str, Any]) -> None:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                webhook_url,
                json=payload,
            )
        response.raise_for_status()
