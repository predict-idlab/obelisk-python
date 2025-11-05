import json
from datetime import datetime, timedelta
from math import floor
from typing import Any, Literal
from collections.abc import AsyncGenerator

import httpx
from pydantic import ValidationError

from obelisk.exceptions import ObeliskError
from obelisk.types import Datapoint, IngestMode, QueryResult, TimestampPrecision

from obelisk.asynchronous.base import BaseClient


class Obelisk(BaseClient):
    """
    Component that contains all the logic to consume data from
    the Obelisk API (e.g. historical data, sse).

    For most usecases, `query` will be the method you need.
    Have a look at `query_time_chunked` too, because it might just be very useful.

    Obelisk API Documentation:
    https://obelisk.docs.apiary.io/
    """

    async def fetch_single_chunk(
        self,
        datasets: list[str],
        metrics: list[str] | None = None,
        fields: list[str] | None = None,
        from_timestamp: int | None = None,
        to_timestamp: int | None = None,
        order_by: dict[str, Any] | None = None,
        filter_: dict[str, Any] | None = None,
        limit: int | None = None,
        limit_by: dict[str, Any] | None = None,
        cursor: str | None = None,
    ) -> QueryResult:
        """
        Queries one chunk of events from Obelisk for given parameters,
        does not handle paging over Cursors.

        Parameters
        ----------

        - datasets:
            List of Dataset IDs.
        - metrics:
            List of Metric IDs or wildcards (e.g. `*::number`), defaults to all metrics.
        - fields:
            List of fields to return in the result set.
            Defaults to `[metric, source, value]`
        - from_timestamp:
            Limit output to events after (and including)
            this UTC millisecond timestamp, if present.
        - to_timestamp:
            Limit output to events before (and excluding)
            this UTC millisecond timestamp, if present.
        - order_by:
            Specifies the ordering of the output,
            defaults to ascending by timestamp.
            See Obelisk docs for format. Caller is responsible for validity.
        - filter_:
            Limit output to events matching the specified Filter expression.
            See Obelisk docs, caller is responsible for validity.
        - limit:
            Limit output to a maximum number of events.
            Also determines the page size.
            Default is server-determined, usually 2500.
        - limit_by:
            Limit the combination of a specific set of Index fields
            to a specified maximum number.
        - cursor:
            Specifies the next cursor,
            used when paging through large result sets.
        """

        # pylint: disable=too-many-arguments
        data_range = {"datasets": datasets}
        if metrics is not None:
            data_range["metrics"] = metrics

        payload = {
            "dataRange": data_range,
            "cursor": cursor,
            "fields": fields,
            "from": from_timestamp,
            "to": to_timestamp,
            "orderBy": order_by,
            "filter": filter_,
            "limit": limit,
            "limitBy": limit_by,
        }
        response = await self.http_post(
            self.kind.query_url,
            data={k: v for k, v in payload.items() if v is not None},
        )
        if response.status_code != 200:
            self.log.warning(f"Unexpected status code: {response.status_code}")
            raise ObeliskError(response.status_code, response.reason_phrase)

        try:
            js = response.json()
            return QueryResult.model_validate(js)
        except json.JSONDecodeError as e:
            msg = f"Obelisk response is not a JSON object: {e}"
            self.log.warning(msg)
            raise ObeliskError(msg) from e
        except ValidationError as e:
            msg = f"Response cannot be validated: {e}"
            self.log.warning(msg)
            raise ObeliskError(msg) from e

    async def query(
        self,
        datasets: list[str],
        metrics: list[str] | None = None,
        fields: list[str] | None = None,
        from_timestamp: int | None = None,
        to_timestamp: int | None = None,
        order_by: dict[str, Any] | None = None,
        filter_: dict[str, Any] | None = None,
        limit: int | None = None,
        limit_by: dict[str, Any] | None = None,
    ) -> list[Datapoint]:
        """
        Queries data from obelisk,
        automatically iterating when a cursor is returned.

        Parameters
        ----------

        - datasets:
            List of Dataset IDs.
        - metrics:
            List of Metric IDs or wildcards (e.g. `*::number`), defaults to all metrics.
        - fields:
            List of fields to return in the result set.
            Defaults to `[metric, source, value]`
        - from_timestamp:
            Limit output to events after (and including)
            this UTC millisecond timestamp, if present.
        - to_timestamp:
            Limit output to events before (and excluding)
            this UTC millisecond timestamp, if present.
        - order_by:
            Specifies the ordering of the output,
            defaults to ascending by timestamp.
            See Obelisk docs for format. Caller is responsible for validity.
        - filter_:
            Limit output to events matching the specified Filter expression.
            See Obelisk docs, caller is responsible for validity.
        - limit:
            Limit output to a maximum number of events.
            Also determines the page size.
            Default is server-determined, usually 2500.
        - limit_by:
            Limit the combination of a specific set of Index fields
            to a specified maximum number.
        """

        cursor: str | None | Literal[True] = True
        result_set: list[Datapoint] = []

        while cursor:
            actual_cursor = cursor if cursor is not True else None
            result: QueryResult = await self.fetch_single_chunk(
                datasets=datasets,
                metrics=metrics,
                fields=fields,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
                order_by=order_by,
                filter_=filter_,
                limit=limit,
                limit_by=limit_by,
                cursor=actual_cursor,
            )
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

    async def query_time_chunked(
        self,
        datasets: list[str],
        metrics: list[str],
        from_time: datetime,
        to_time: datetime,
        jump: timedelta,
        filter_: dict[str, Any] | None = None,
        direction: Literal["asc", "desc"] = "asc",
    ) -> AsyncGenerator[list[Datapoint], None]:
        """
        Fetches all data matching the provided filters,
        yielding one chunk at a time.
        One "chunk" may require several Obelisk calls to resolve cursors.
        By necessity iterates over time, no other ordering is supported.

        Parameters
        ----------

        - datasets:
            Dataset IDs to query from
        - metrics:
            IDs of metrics to query
        - from_time:
            Start time to fetch from
        - to_time:
            End time to fetch until.
        - jump:
            Size of one yielded chunk
        - filter_:
            Obelisk filter, caller is responsible for correct format
        - direction:
            Yield older data or newer data first, defaults to older first.
        """

        current_start = from_time
        while current_start < to_time:
            yield await self.query(
                datasets=datasets,
                metrics=metrics,
                from_timestamp=floor(current_start.timestamp() * 1000),
                to_timestamp=floor((current_start + jump).timestamp() * 1000 - 1),
                order_by={"field": ["timestamp"], "ordering": direction},
                filter_=filter_,
            )
            current_start += jump

    async def send(
        self,
        dataset: str,
        data: list[dict[str, Any]],
        precision: TimestampPrecision = TimestampPrecision.MILLISECONDS,
        mode: IngestMode = IngestMode.DEFAULT,
    ) -> httpx.Response:
        """
        Publishes data to Obelisk

        Parameters
        ----------
        - dataset:
            ID for the dataset to publish to
        - data:
            List of Obelisk-acceptable datapoints.
            Exact format varies between Classic or HFS,
            caller is responsible for formatting.
        - precision:
            Precision used in the numeric timestamps contained in data.
            Ensure it matches to avoid weird errors.
        - mode:
            See docs for `obelisk.types.IngestMode`.

        Raises
        ------

        ObeliskError
            When the resulting status code is not 204, an empty `obelisk.exceptions.ObeliskError` is raised.
        """

        params = {
            "datasetId": dataset,
            "timestampPrecision": precision.value,
            "mode": mode.value,
        }

        response = await self.http_post(
            f"{self.kind.ingest_url}/{dataset}", data=data, params=params
        )
        if response.status_code != 204:
            msg = f"An error occured during data ingest. Status {response.status_code}, message: {response.text}"
            self.log.warning(msg)
            raise ObeliskError(msg)
        return response
