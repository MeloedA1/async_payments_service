from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.domain.enums import Currency, PaymentStatus
from src.entrypoints.consumer.outbox_publisher import publish_outbox
from src.services.payment_processing import PaymentProcessingService


@pytest.mark.parametrize(
    'prepared_models',
    [
        {
            'models': {
                'payment_1': {
                    '_model': 'payments',
                    'id': UUID('4564bf21-c030-46c1-8faf-d4b0e1eb1ffd'),
                    'amount': '1500',
                    'currency': Currency.EUR,
                },
                'payment_2': {
                    '_model': 'payments',
                    'id': UUID('7774bf21-c030-46c1-8faf-d4b0e1eb1ffd'),
                    'amount': '4200',
                    'currency': Currency.RUB,
                },
                'outbox_1': {'_model': 'outbox', 'payload': {'payment_id': '4564bf21-c030-46c1-8faf-d4b0e1eb1ffd'}},
                'outbox_2': {'_model': 'outbox', 'payload': {'payment_id': '7774bf21-c030-46c1-8faf-d4b0e1eb1ffd'}},
            }
        }
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_outbox_publisher(prepared_models):
    uow = prepared_models['uow']
    broker = AsyncMock()

    async with uow:
        unpublished_before = await uow.outbox.get_unpublished()
        assert len(unpublished_before) == 2

    await publish_outbox(
        uow=uow,
        broker=broker,
        limit=10,
    )

    assert broker.publish.await_count == 2

    async with uow:
        unpublished_after = await uow.outbox.get_unpublished()
        all_events = await uow.outbox.get_all()

        assert len(unpublished_after) == 0
        assert all(event.published is True for event in all_events)
        assert all(event.published_at is not None for event in all_events)


@pytest.mark.parametrize(
    'prepared_models',
    [
        {
            'models': {
                'payment_1': {
                    '_model': 'payments',
                    'id': UUID('4564bf21-c030-46c1-8faf-d4b0e1eb1ffd'),
                    'amount': '1500',
                    'currency': Currency.EUR,
                },
                'payment_2': {
                    '_model': 'payments',
                    'id': UUID('7774bf21-c030-46c1-8faf-d4b0e1eb1ffd'),
                    'amount': '4200',
                    'currency': Currency.RUB,
                },
                'outbox_1': {'_model': 'outbox', 'payload': {'payment_id': '4564bf21-c030-46c1-8faf-d4b0e1eb1ffd'}},
                'outbox_2': {'_model': 'outbox', 'payload': {'payment_id': '7774bf21-c030-46c1-8faf-d4b0e1eb1ffd'}},
            }
        }
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_payment_processing_service(
    prepared_models,
):
    uow = prepared_models['uow']

    async with uow:
        payments = await uow.payments.get_all()
        payment = payments[0]
        payment_id = payment.id

        assert payment.status == PaymentStatus.PENDING
        assert payment.processed_at is None

    service = PaymentProcessingService(uow=uow)

    service._emulate_payment_gateway = AsyncMock(
        return_value=PaymentStatus.SUCCEEDED,
    )
    service._send_webhook_with_retry = AsyncMock()

    await service.process(payment_id)

    async with uow:
        processed_payment = await uow.payments.get_by_id(payment_id)

        assert processed_payment.status == PaymentStatus.SUCCEEDED
        assert processed_payment.processed_at is not None

    service._send_webhook_with_retry.assert_awaited_once()

    call_kwargs = service._send_webhook_with_retry.await_args.kwargs

    assert call_kwargs['webhook_url'] == processed_payment.webhook_url
    assert call_kwargs['payload']['payment_id'] == str(payment_id)
    assert call_kwargs['payload']['status'] == PaymentStatus.SUCCEEDED
