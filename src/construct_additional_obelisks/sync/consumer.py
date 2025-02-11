import asyncio
from datetime import datetime, timedelta
from typing import List, Literal, Generator

from src.construct_additional_obelisks.asynchronous.consumer import \
    Consumer as AsyncConsumer
from src.construct_additional_obelisks.strategies.retry import RetryStrategy, \
    NoRetryStrategy
from src.construct_additional_obelisks.types import QueryResult, Datapoint, ObeliskKind


class Consumer:
    loop: asyncio.AbstractEventLoop
    async_consumer: AsyncConsumer

    def __init__(self, client: str, secret: str,
                 retry_strategy: RetryStrategy = NoRetryStrategy(),
                 kind: ObeliskKind = ObeliskKind.CLASSIC):
        self.async_consumer = AsyncConsumer(client, secret, retry_strategy, kind)
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


def query_time_chunked(self, datasets: List[str], metrics: List[str],
                       from_time: datetime, to_time: datetime,
                       jump: timedelta, filter_: dict | None = None,
                       direction: Literal['asc', 'desc'] = 'asc'
                       ) -> Generator[List[Datapoint], None, None]:
    """
    Fetches data from Obelisk in groups by time, one `jump` at a time.
    Each iteration may cause more than one network query.
    """

    current_start = from_time
    while current_start < to_time:
        yield self.query(datasets=datasets, metrics=metrics,
                               from_timestamp=current_start.timestamp(),
                               to_timestamp=(current_start + jump).timestamp() - 1,
                               order_by={"field": ["timestamp"], "ordering": direction},
                               filter_=filter_)
        current_start += jump
