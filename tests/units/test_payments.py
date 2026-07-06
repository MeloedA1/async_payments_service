import logging
from uuid import UUID

import pytest

from src.domain.enums import Currency
from src.schemas.payments import PaymentCreateRequest
from src.services.payments import add_payment
from src.services.uow import Uow

logger = logging.getLogger('default')


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
async def test_payment_and_outbox_creation(prepared_models: dict):
    uow: Uow = prepared_models['uow']
    body = PaymentCreateRequest(
        amount=50,
        currency=Currency.USD,
        description='New',
        metadata={'info': 'New payment'},
        webhook_url='https://webhook.site/',
    )
    # Проверка количества записей до создания нового платежа
    async with uow:
        payments = await uow.payments.get_all()
        outbox = await uow.outbox.get_all()
        assert len(payments) == 2
        assert len(outbox) == 2

    # Создание нового платежа
    new_payment = await add_payment(uow=uow, request=body, idempotency_key='123')
    new_payment_idempotency_key = new_payment.idempotency_key
    async with uow:
        payments = await uow.payments.get_all()
        outbox = await uow.outbox.get_all()
        assert len(payments) == 3
        assert len(outbox) == 3

    # Повторная попытка создать платеж - с тем же idempotency_key='123' еще раз не создастся
    repeated_payment = await add_payment(uow=uow, request=body, idempotency_key='123')
    assert repeated_payment.id == new_payment.id
    assert repeated_payment.idempotency_key == new_payment_idempotency_key
    async with uow:
        payments = await uow.payments.get_all()
        outbox = await uow.outbox.get_all()
        assert len(payments) == 3
        assert len(outbox) == 3
