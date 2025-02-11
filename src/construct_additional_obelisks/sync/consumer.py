import asyncio
from typing import List

from src.construct_additional_obelisks.asynchronous.consumer import \
    Consumer as AsyncConsumer
from src.construct_additional_obelisks.types import QueryResult, Datapoint


class Consumer:
    loop: asyncio.AbstractEventLoop
    async_consumer: AsyncConsumer

    def __init__(self, client: str, secret: str):
        self.async_consumer = AsyncConsumer(client, secret)
        self.loop = asyncio.get_event_loop()

    def single_chunk(self, datasets: List[str], metrics: List[str] | None = None,
                     fields: dict | None = None,
                     from_timestamp: int | None = None, to_timestamp: int | None = None,
                     order_by: dict | None = None,
                     filter_: dict | None = None,
                     limit: int | None = None, limit_by: dict | None = None,
                     cursor: str | None = None) -> QueryResult:
        task = self.loop.create_task(
            self.async_consumer.single_chunk(datasets, metrics, fields, from_timestamp,
                                             to_timestamp, order_by, filter_,
                                             limit, limit_by, cursor))
        return self.loop.run_until_complete(task)


def query(self, datasets: List[str], metrics: List[str] | None = None,
          fields: dict | None = None,
          from_timestamp: int | None = None,
          to_timestamp: int | None = None,
          order_by: dict | None = None,
          filter_: dict | None = None,
          limit: int | None = None,
          limit_by: dict | None = None) -> List[Datapoint]:
    task = self.loop.create_task(
        self.async_consumer.query(datasets, metrics, fields, from_timestamp,
                                  to_timestamp, order_by, filter_, limit,
                                  limit_by))
    return self.loop.run_until_complete(task)
