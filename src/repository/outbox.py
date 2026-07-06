from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import Outbox
from src.repository.base import BaseSQLAlchemyRepository


class OutboxRepo(BaseSQLAlchemyRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session, model_cls=Outbox)

    async def get_unpublished(self, limit: int | None = None) -> list[Outbox]:
        q = select(Outbox).where(Outbox.published.is_(False)).order_by(Outbox.created_at.asc(), Outbox.id.asc())
        if limit:
            q = q.limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all())
