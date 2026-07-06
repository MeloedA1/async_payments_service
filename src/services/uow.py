from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from src.config import settings
from src.repository.outbox import OutboxRepo
from src.repository.payments import PaymentsRepo


def get_engine(db_name):
    return create_async_engine(
        URL.create(
            'postgresql+asyncpg',
            username=settings.db_user,
            password=settings.db_password,
            host=settings.db_host,
            port=settings.db_port,
            database=db_name,
        ),
        pool_pre_ping=True,
        pool_size=30,
        max_overflow=30,
    )


def get_session_factory(engine):
    return async_sessionmaker(autoflush=False, bind=engine, class_=AsyncSession)


session_factory = get_session_factory(engine=get_engine(db_name=settings.db_name))


class Uow:
    def __init__(self, session_factory=session_factory):
        self.session_factory = session_factory

    async def __aenter__(self):
        self._session = self.session_factory()
        self.payments = PaymentsRepo(session=self._session)
        self.outbox = OutboxRepo(session=self._session)
        return self

    @property
    def session(self) -> AsyncSession:
        if not self._session:
            raise RuntimeError('Session does not exist, please use uow as context manager.')
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                await self.rollback()
        finally:
            self.session.expunge_all()
            await self.session.close()
            self._session = None

    async def commit(self):
        await self.session.commit()

    async def refresh(self, obj):
        await self.session.refresh(obj)

    async def rollback(self):
        await self.session.rollback()
