import asyncio
from typing import List

import httpx

from construct_additional_obelisks.asynchronous.producer import \
    Producer as AsyncProducer
from construct_additional_obelisks.strategies.retry import RetryStrategy, \
    NoRetryStrategy
from construct_additional_obelisks.types import IngestMode, TimestampPrecision, \
    ObeliskKind


class Producer:
    loop: asyncio.AbstractEventLoop
    async_producer: AsyncProducer

    def __init__(self, client: str, secret: str,
                 retry_strategy: RetryStrategy = NoRetryStrategy(),
                 kind: ObeliskKind = ObeliskKind.CLASSIC):
        self.async_producer = AsyncProducer(client, secret, retry_strategy, kind)
        self.loop = asyncio.get_event_loop()

    def send(self, dataset: str, data: List[dict],
             precision: TimestampPrecision = TimestampPrecision.MILLISECONDS,
             mode: IngestMode = IngestMode.DEFAULT) -> httpx.Response:
        task = self.loop.create_task(
            self.async_producer.send(dataset, data, precision, mode))
        return self.loop.run_until_complete(task)
