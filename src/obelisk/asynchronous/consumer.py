import json
from datetime import datetime, timedelta
from typing import List, Literal, Generator, Optional

from pydantic import ValidationError

from obelisk.asynchronous.client import Client
from obelisk.exceptions import ObeliskError
from obelisk.types import QueryResult, Datapoint

from math import floor


class Consumer(Client):
    """
    Component that contains all the logic to consume data from
    the Obelisk API (e.g. historical data, sse).

    Obelisk API Documentation:
    https://obelisk.docs.apiary.io/
    """

    async def single_chunk(self, datasets: List[str], metrics: Optional[List[str]] = None,
                           fields: Optional[List[str]] = None,
                           from_timestamp: Optional[int] = None,
                           to_timestamp: Optional[int] = None,
                           order_by: Optional[dict] = None,
                           filter_: Optional[dict] = None,
                           limit: Optional[int] = None,
                           limit_by: Optional[dict] = None,
                           cursor: Optional[str] = None) -> QueryResult:
        """
        Queries one chunk of events from Obelisk for given parameters,
        does not handle paging over Cursors.

        Parameters
        ----------

        datasets : List[str]
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
        cursor : Optional[str] = None
            Specifies the next cursor,
            used when paging through large result sets.
        """

        # pylint: disable=too-many-arguments
        data_range = {
            'datasets': datasets
        }
        if metrics is not None:
            data_range['metrics'] = metrics

        payload = {
            'dataRange': data_range,
            'cursor': cursor,
            'fields': fields,
            'from': from_timestamp,
            'to': to_timestamp,
            'orderBy': order_by,
            'filter': filter_,
            'limit': limit,
            'limitBy': limit_by
        }
        response = await self.http_post(self._events_url,
                                        data={k: v for k, v in payload.items() if
                                              v is not None})
        if response.status_code != 200:
            self.log.warning(f"Unexpected status code: {response.status_code}")
            raise ObeliskError(response.status_code, response.reason_phrase)

        try:
            js = response.json()
            return QueryResult.model_validate(js)
        except json.JSONDecodeError as e:
            msg = f'Obelisk response is not a JSON object: {e}'
            self.log.warning(msg)
            raise ObeliskError(msg)
        except ValidationError as e:
            msg = f"Response cannot be validated: {e}"
            self.log.warning(msg)
            raise ObeliskError(msg)


    async def query(self, datasets: List[str], metrics:Optional[List[str]] = None,
                    fields:Optional[List[str]] = None,
                    from_timestamp: Optional[int] = None, to_timestamp: Optional[int] = None,
                    order_by: Optional[dict] = None,
                    filter_: Optional[dict] = None,
                    limit: Optional[int] = None,
                    limit_by: Optional[dict] = None) -> List[Datapoint]:
        """
        Queries data from obelisk,
        automatically iterating when a cursor is returned.

        Parameters
        ----------

        datasets : List[str]
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

        cursor: Optional[str] | Literal[True] = True
        result_set: List[Datapoint] = []

        while cursor:
            actual_cursor = cursor if cursor is not True else None
            result: QueryResult = await self.single_chunk(datasets=datasets,
                                                        metrics=metrics, fields=fields,
                                                        from_timestamp=from_timestamp,
                                                        to_timestamp=to_timestamp,
                                                        order_by=order_by, filter_=filter_,
                                                        limit=limit,
                                                        limit_by=limit_by,
                                                        cursor=actual_cursor)
            result_set.extend(result.items)
            cursor = result.cursor

            if limit and len(result_set) >= limit:
                """On Obelisk HFS, limit is actually page size,
                so continuing to read the cursor will result in a larger than desired
                set of results.

                On the other hand, if the limit is very large,
                we may need to iterate before we reach the desired limit after all.
                """
                break

        return result_set


    async def query_time_chunked(self, datasets: List[str], metrics: List[str],
                                from_time: datetime, to_time: datetime,
                                jump: timedelta, filter_: Optional[dict] = None,
                                direction: Literal['asc', 'desc'] = 'asc'
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
        from_time : `datetime.datetime`
            Start time to fetch from
        to_time : `datetime.datetime`
            End time to fetch until.
        jump : `datetime.timedelta`
            Size of one yielded chunk
        filter_ : Optional[dict] = None
            Obelisk filter, caller is responsible for correct format
        direction : Literal['asc', 'desc'] = 'asc'
            Yield older data or newer data first, defaults to older first.
        """

        current_start = from_time
        while current_start < to_time:
            yield await self.query(datasets=datasets, metrics=metrics,
                                from_timestamp=floor(current_start.timestamp() * 1000),
                                to_timestamp=floor((current_start + jump).timestamp() * 1000 - 1),
                                order_by={"field": ["timestamp"], "ordering": direction},
                                filter_=filter_)
            current_start += jump
