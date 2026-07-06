import uuid
from datetime import UTC, datetime
from decimal import Decimal

from faker import Faker

from src.domain import models
from src.schemas.payments import OUTBOX_EVENT_TYPE

fake = Faker()


def make_payment(**kwargs) -> models.Payment:
    return models.Payment(
        **{
            'id': uuid.uuid4(),
            'amount': Decimal(fake.pydecimal(left_digits=4, right_digits=2, positive=True)),
            'currency': models.Currency.RUB,
            'description': fake.sentence(),
            'meta': {
                'order_id': fake.uuid4(),
                'customer': fake.name(),
            },
            'status': models.PaymentStatus.PENDING,
            'idempotency_key': str(uuid.uuid4()),
            'webhook_url': fake.url(),
            'created_at': datetime.now(UTC),
            'processed_at': None,
            **kwargs,
        }
    )


def make_outbox(**kwargs) -> models.Outbox:
    return models.Outbox(
        **{
            'id': uuid.uuid4(),
            'event_type': OUTBOX_EVENT_TYPE,
            'payload': {
                'payment_id': str(uuid.uuid4()),
            },
            'published': False,
            'created_at': datetime.now(UTC),
            'published_at': None,
            **kwargs,
        }
    )
