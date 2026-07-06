import uuid
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Security, status

from src.entrypoints.dependencies.auth import verify_api_key
from src.entrypoints.dependencies.uow import get_uow
from src.schemas.payments import PaymentCreateRequest, PaymentCreateResponse, PaymentResponse
from src.services.payments import add_payment, get_payment
from src.services.uow import Uow

payments_router = APIRouter(prefix='/api/v1/payments', tags=['Payments'], dependencies=[Security(verify_api_key)])


@payments_router.post('', response_model=PaymentCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_payment(
    body: PaymentCreateRequest,
    idempotency_key: Annotated[str, Header(alias='Idempotency-Key')],
    uow: Uow = Depends(get_uow),
) -> PaymentCreateResponse:

    payment = await add_payment(
        uow=uow,
        request=body,
        idempotency_key=idempotency_key,
    )

    return PaymentCreateResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )


@payments_router.get('/{payment_id}', response_model=PaymentResponse)
async def _get_payment(
    payment_id: uuid.UUID,
    uow: Uow = Depends(get_uow),
) -> PaymentResponse:
    payment = await get_payment(uow, payment_id)

    if payment is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Payment not found',
        )

    return PaymentResponse.model_validate(payment)
