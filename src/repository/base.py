from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.exceptions import NotFoundException


class BaseSQLAlchemyRepository:
    def __init__(self, session: AsyncSession, model_cls) -> None:
        self.session = session
        self.model_cls = model_cls

    def add(self, obj: Any) -> Any:
        self.session.add(obj)
        return obj

    async def get(self, field: str, value: Any) -> Any | None:
        stmt = select(self.model_cls).where(getattr(self.model_cls, field) == value)
        return (await self.session.execute(stmt)).scalars().first()

    async def get_or_error(self, instance_id: int) -> Any:
        if instance := await self.get("id", instance_id):
            return instance
        raise NotFoundException(f"{self.model_cls.__name__} with id {instance_id} not found")

    async def get_all(self):
        q = select(self.model_cls)
        return (await self.session.execute(q)).scalars().all()
