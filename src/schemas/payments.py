import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.domain.enums import Currency, PaymentStatus

OUTBOX_EVENT_TYPE = 'payment_created'


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0, examples=['1500.50'])
    currency: Currency
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: HttpUrl


class PaymentCreateResponse(BaseModel):
    payment_id: uuid.UUID
    status: PaymentStatus
    created_at: datetime


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: Decimal = Field(examples=['1500.50'])
    currency: Currency
    description: str
    metadata: dict[str, Any] = Field(alias='meta')
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None
