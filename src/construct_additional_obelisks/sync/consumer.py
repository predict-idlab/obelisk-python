import asyncio
from datetime import datetime, timedelta
from typing import List, Literal, Generator

from construct_additional_obelisks.asynchronous.consumer import \
    Consumer as AsyncConsumer
from construct_additional_obelisks.strategies.retry import RetryStrategy, \
    NoRetryStrategy
from construct_additional_obelisks.types import QueryResult, Datapoint, ObeliskKind


class Consumer:
    """
    Component that contains all the logic to consume data from
    the Obelisk API (e.g. historical data, sse).

    Obelisk API Documentation:
    https://obelisk.docs.apiary.io/
    """

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
        """
        Queries one chunk of events from Obelisk for given parameters,
        does not handle paging over Cursors.

        Parameters
        ----------

        datasets : List[str]
            List of Dataset IDs.
        metrics: List[str] | None = None
            List of Metric IDs or wildcards (e.g. `*::number`), defaults to all metrics.
        fields: List[str] | None = None
            List of fields to return in the result set.
            Defaults to `[metric, source, value]`
        from_timestamp: int | None = None
            Limit output to events after (and including)
            this UTC millisecond timestamp, if present.
        to_timestamp: int | None = None
            Limit output to events before (and excluding)
            this UTC millisecond timestamp, if present.
        order_by: dict | None = None
            Specifies the ordering of the output,
            defaults to ascending by timestamp.
            See Obelisk docs for format. Caller is responsible for validity.
        filter_: dict | None = None
            Limit output to events matching the specified Filter expression.
            See Obelisk docs, caller is responsible for validity.
        limit: int | None = None
            Limit output to a maximum number of events.
            Also determines the page size.
            Default is server-determined, usually 2500.
        limit_by: dict | None = None
            Limit the combination of a specific set of Index fields
            to a specified maximum number.
        cursor: str | None = None
            Specifies the next cursor,
            used when paging through large result sets.
        """

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
        """
        Queries data from obelisk,
        automatically iterating when a cursor is returned.

        Parameters
        ----------

        datasets : List[str]
            List of Dataset IDs.
        metrics: List[str] | None = None
            List of Metric IDs or wildcards (e.g. `*::number`), defaults to all metrics.
        fields: List[str] | None = None
            List of fields to return in the result set.
            Defaults to `[metric, source, value]`
        from_timestamp: int | None = None
            Limit output to events after (and including)
            this UTC millisecond timestamp, if present.
        to_timestamp: int | None = None
            Limit output to events before (and excluding)
            this UTC millisecond timestamp, if present.
        order_by: dict | None = None
            Specifies the ordering of the output,
            defaults to ascending by timestamp.
            See Obelisk docs for format. Caller is responsible for validity.
        filter_: dict | None = None
            Limit output to events matching the specified Filter expression.
            See Obelisk docs, caller is responsible for validity.
        limit: int | None = None
            Limit output to a maximum number of events.
            Also determines the page size.
            Default is server-determined, usually 2500.
        limit_by: dict | None = None
            Limit the combination of a specific set of Index fields
            to a specified maximum number.
        """

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
        Fetches all data matching the provided filters,
        yielding one chunk at a time.
        One "chunk" may require several Obelisk calls to resolve cursors.
        By necessity iterates over time, no other ordering is supported.

        Parameters
        ----------

        datasets: List[str]
            Dataset IDs to query from
        metrics: List[str]
            IDs of metrics to query
        from_time: `datetime.timedelta`
            Start time to fetch from
        to_time: `datetime.timedelta`
            End time to fetch until.
        jump: `datetime.timedelta`
            Size of one yielded chunk
        filter_: dict | None = None
            Obelisk filter, caller is responsible for correct format
        direction: Literal['asc', 'desc'] = 'asc'
            Yield older data or newer data first, defaults to older first.
        """

        current_start = from_time
        while current_start < to_time:
            yield self.query(datasets=datasets, metrics=metrics,
                                from_timestamp=current_start.timestamp(),
                                to_timestamp=(current_start + jump).timestamp() - 1,
                                order_by={"field": ["timestamp"], "ordering": direction},
                                filter_=filter_)
            current_start += jump
