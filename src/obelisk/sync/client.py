import asyncio
from datetime import datetime, timedelta
from math import floor
from typing import Generator, List, Literal, Optional

import httpx

from obelisk.asynchronous import Obelisk as AsyncObelisk
from obelisk.strategies.retry import NoRetryStrategy, RetryStrategy
from obelisk.types import (
    Datapoint,
    IngestMode,
    ObeliskKind,
    QueryResult,
    TimestampPrecision,
)


class Obelisk:
    """
    Component that contains all the logic to consume data from
    the Obelisk API (e.g. historical data, sse).

    Wraps :class:`~obelisk.asynchronous.consumer.Consumer`.

    Obelisk API Documentation:
    https://obelisk.docs.apiary.io/
    """

    loop: asyncio.AbstractEventLoop
    """Event loop used to run interal async operations"""
    async_obelisk: AsyncObelisk
    """The actual implementation this synchronous wrapper refers to"""

    def __init__(
        self,
        client: str,
        secret: str,
        retry_strategy: RetryStrategy = NoRetryStrategy(),
        kind: ObeliskKind = ObeliskKind.CLASSIC,
    ):
        self.async_obelisk = AsyncObelisk(client, secret, retry_strategy, kind)
        self.loop = asyncio.get_event_loop()

    def fetch_single_chunk(
        self,
        datasets: List[str],
        metrics: Optional[List[str]] = None,
        fields: Optional[dict] = None,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        order_by: Optional[dict] = None,
        filter_: Optional[dict] = None,
        limit: Optional[int] = None,
        limit_by: Optional[dict] = None,
        cursor: Optional[str] = None,
    ) -> QueryResult:
        """
        Queries one chunk of events from Obelisk for given parameters,
        does not handle paging over Cursors.

        Parameters
        ----------

        datasets : List[str]
            List of Dataset IDs.
        metrics : Optional[List[str]] = None
            List of Metric IDs or wildcards (e.g. ``*::number``), defaults to all metrics.
        fields : Optional[List[str]] = None
            List of fields to return in the result set.
            Defaults to `[metric, source, value]`
        from_timestamp : Optional[int] = None
            Limit output to events after (and including)
            this UTC millisecond timestamp, if present.
        to_timestamp : Optional[int] = None
            Limit output to events before (and excluding)
            this UTC millisecond timestamp, if present.
        order_by : Optional[dict] = None
            Specifies the ordering of the output,
            defaults to ascending by timestamp.
            See Obelisk docs for format. Caller is responsible for validity.
        filter_ : Optional[dict] = None
            Limit output to events matching the specified Filter expression.
            See Obelisk docs, caller is responsible for validity.
        limit : Optional[int] = None
            Limit output to a maximum number of events.
            Also determines the page size.
            Default is server-determined, usually 2500.
        limit_by : Optional[dict] = None
            Limit the combination of a specific set of Index fields
            to a specified maximum number.
        cursor : Optional[str] = None
            Specifies the next cursor,
            used when paging through large result sets.
        """

        self.async_obelisk.log.info("Starting task")
        task = self.loop.create_task(
            self.async_obelisk.fetch_single_chunk(
                datasets,
                metrics,
                fields,
                from_timestamp,
                to_timestamp,
                order_by,
                filter_,
                limit,
                limit_by,
                cursor,
            )
        )
        self.async_obelisk.log.info("Blocking...")
        return self.loop.run_until_complete(task)

    def query(
        self,
        datasets: List[str],
        metrics: Optional[List[str]] = None,
        fields: Optional[dict] = None,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        order_by: Optional[dict] = None,
        filter_: Optional[dict] = None,
        limit: Optional[int] = None,
        limit_by: Optional[dict] = None,
    ) -> List[Datapoint]:
        """
        Queries data from obelisk,
        automatically iterating when a cursor is returned.

        Parameters
        ----------

        datasets  : List[str]
            List of Dataset IDs.
        metrics : Optional[List[str]] = None
            List of Metric IDs or wildcards (e.g. `*::number`), defaults to all metrics.
        fields : Optional[List[str]] = None
            List of fields to return in the result set.
            Defaults to `[metric, source, value]`
        from_timestamp : Optional[int] = None
            Limit output to events after (and including)
            this UTC millisecond timestamp, if present.
        to_timestamp : Optional[int] = None
            Limit output to events before (and excluding)
            this UTC millisecond timestamp, if present.
        order_by : Optional[dict] = None
            Specifies the ordering of the output,
            defaults to ascending by timestamp.
            See Obelisk docs for format. Caller is responsible for validity.
        filter_ : Optional[dict] = None
            Limit output to events matching the specified Filter expression.
            See Obelisk docs, caller is responsible for validity.
        limit : Optional[int] = None
            Limit output to a maximum number of events.
            Also determines the page size.
            Default is server-determined, usually 2500.
        limit_by : Optional[dict] = None
            Limit the combination of a specific set of Index fields
            to a specified maximum number.
        """

        task = self.loop.create_task(
            self.async_obelisk.query(
                datasets,
                metrics,
                fields,
                from_timestamp,
                to_timestamp,
                order_by,
                filter_,
                limit,
                limit_by,
            )
        )
        return self.loop.run_until_complete(task)

    def query_time_chunked(
        self,
        datasets: List[str],
        metrics: List[str],
        from_time: datetime,
        to_time: datetime,
        jump: timedelta,
        filter_: Optional[dict] = None,
        direction: Literal["asc", "desc"] = "asc",
    ) -> Generator[List[Datapoint], None, None]:
        """
        Fetches all data matching the provided filters,
        yielding one chunk at a time.
        One "chunk" may require several Obelisk calls to resolve cursors.
        By necessity iterates over time, no other ordering is supported.

        Parameters
        ----------

        datasets : List[str]
            Dataset IDs to query from
        metrics : List[str]
            IDs of metrics to query
        from_time : datetime.datetime
            Start time to fetch from
        to_time : datetime.datetime
            End time to fetch until.
        jump : datetime.timedelta
            Size of one yielded chunk
        filter_ : Optional[dict] = None
            Obelisk filter, caller is responsible for correct format
        direction : Literal['asc', 'desc'] = 'asc'
            Yield older data or newer data first, defaults to older first.
        """

        current_start = from_time
        while current_start < to_time:
            yield self.query(
                datasets=datasets,
                metrics=metrics,
                from_timestamp=floor(current_start.timestamp() * 1000),
                to_timestamp=floor((current_start + jump).timestamp() * 1000 - 1),
                order_by={"field": ["timestamp"], "ordering": direction},
                filter_=filter_,
            )
            current_start += jump

    def send(
        self,
        dataset: str,
        data: List[dict],
        precision: TimestampPrecision = TimestampPrecision.MILLISECONDS,
        mode: IngestMode = IngestMode.DEFAULT,
    ) -> httpx.Response:
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
            self.async_obelisk.send(dataset, data, precision, mode)
        )
        return self.loop.run_until_complete(task)
