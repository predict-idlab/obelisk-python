import asyncio
from typing import List

import httpx

from obelisk.asynchronous.producer import \
    Producer as AsyncProducer
from obelisk.strategies.retry import RetryStrategy, \
    NoRetryStrategy
from obelisk.types import IngestMode, TimestampPrecision, \
    ObeliskKind


class Producer:
    """
    Synchronous equivalient of :class:`~obelisk.asynchronous.producer.Producer`,
    to publish data to Obelisk.
    """

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
        """
        Publishes data to Obelisk

        Parameters
        ----------
        dataset : str
            ID for the dataset to publish to
        data : List[dict]
            List of Obelisk-acceptable datapoints.
            Exact format varies between Classic or HFS,
            caller is responsible for formatting.
        precision : TimestampPrecision = TimestampPrecision.MILLISECONDS
            Precision used in the numeric timestamps contained in data.
            Ensure it matches to avoid weird errors.
        mode : IngestMode = IngestMode.DEFAULT
            See docs for :class:`~obelisk.types.IngestMode`.

        Raises
        ------

        ObeliskError
            When the resulting status code is not 204, an empty :exc:`~obelisk.exceptions.ObeliskError` is raised.
        """

        task = self.loop.create_task(
            self.async_producer.send(dataset, data, precision, mode))
        return self.loop.run_until_complete(task)
