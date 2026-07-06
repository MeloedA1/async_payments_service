from datetime import UTC, datetime

from aiormq import AMQPError

from src.config import logger
from src.entrypoints.dependencies.uow import get_uow
from src.services.uow import Uow


async def publish_outbox(broker, uow: Uow | None = None, limit: int | None = None) -> None:

    uow = uow or get_uow()

    async with uow:
        events = await uow.outbox.get_unpublished(limit)
        ids = [str(x.id) for x in events]
        logger.info('Were found %s unpublished events: %s', len(ids), ids)

        for event in events:
            try:
                await broker.publish(
                    message=event.payload,
                    queue='payments.new',
                )
            except AMQPError:
                logger.exception('Failed to publish event %s', event.id)
                continue

            event.published = True
            event.published_at = datetime.now(UTC)

            await uow.commit()

            logger.info('Event %s were published', event.id)
