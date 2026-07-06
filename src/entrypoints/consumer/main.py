import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from faststream import FastStream

from src.entrypoints.consumer import payment_consumer
from src.entrypoints.consumer.outbox_publisher import publish_outbox
from src.entrypoints.consumer.payment_consumer import payments_dlq
from src.entrypoints.dependencies.rabbit import broker

app = FastStream(broker)


async def main() -> None:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        publish_outbox,
        'interval',
        seconds=2,
        kwargs={
            'broker': broker,
            'limit': 10,
        },
    )

    scheduler.start()

    await broker.connect()
    await broker.declare_queue(payments_dlq)

    await app.run()


if __name__ == '__main__':
    asyncio.run(main())
