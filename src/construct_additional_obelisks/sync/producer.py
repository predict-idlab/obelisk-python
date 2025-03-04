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
        self.loop = asyncio.new_event_loop()

    def send(self, dataset: str, data: List[dict],
             precision: TimestampPrecision = TimestampPrecision.MILLISECONDS,
             mode: IngestMode = IngestMode.DEFAULT) -> httpx.Response:
        """
        Publishes data to Obelisk

        Parameters
        ----------
        dataset: str
            ID for the dataset to publish to
        data: List[dict]
            List of Obelisk-acceptable datapoints.
            Exact format varies between Classic or HFS,
            caller is responsible for formatting.
        precision: TimestampPrecision = TimestampPrecision.MILLISECONDS
            Precision used in the numeric timestamps contained in data.
            Ensure it matches to avoid weird errors.
        mode: IngestMode = IngestMode.DEFAULT
            See docs for `construct_additional_obelisks.types.IngestMode`.

        Raises
        ------

        ObeliskError
            When the resulting status code is not 204, an empty `construct_additional_obelisks.exceptions.ObeliskError` is raised.
        """

        task = self.loop.create_task(
            self.async_producer.send(dataset, data, precision, mode))
        return self.loop.run_until_complete(task)
