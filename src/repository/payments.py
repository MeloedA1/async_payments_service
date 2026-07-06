from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import Payment
from src.repository.base import BaseSQLAlchemyRepository


class PaymentsRepo(BaseSQLAlchemyRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session, model_cls=Payment)

    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Payment | None:
        q = select(Payment).where(Payment.idempotency_key == idempotency_key)
        return (await self.session.execute(q)).scalar()

    async def get_by_id(
        self,
        payment_id: UUID,
    ) -> Payment | None:
        q = select(Payment).where(Payment.id == payment_id)
        return (await self.session.execute(q)).scalar()
