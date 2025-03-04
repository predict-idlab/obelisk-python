import json
from datetime import datetime, timedelta
from typing import List, Literal, Generator

from pydantic import ValidationError

from construct_additional_obelisks.asynchronous.client import Client
from construct_additional_obelisks.exceptions import ObeliskError
from construct_additional_obelisks.types import QueryResult, Datapoint


class Consumer(Client):
    """
    Component that contains all the logic to consume data from
    the Obelisk API (e.g. historical data, sse).

    Obelisk API Documentation:
    https://obelisk.docs.apiary.io/
    """

    async def single_chunk(self, datasets: List[str], metrics: List[str] | None = None,
                           fields: dict | None = None,
                           from_timestamp: int | None = None,
                           to_timestamp: int | None = None,
                           order_by: dict | None = None,
                           filter_: dict | None = None,
                           limit: int | None = None,
                           limit_by: dict | None = None,
                           cursor: str | None = None) -> QueryResult:
        """
        Queries one chunk of events from Obelisk for given parameters

        :param datasets: List of Dataset IDs.
        :param metrics: List of Metric IDs or wildcards (e.g. `*::number`).
        :param fields: List of fields to return in the result set.
            Defaults to `[metric, source, value]`
        :param from_timestamp: Limit output to events after (and including)
            this UTC millisecond timestamp.
        :param to_timestamp: Limit output to events before (and excluding)
            this UTC millisecond timestamp.
        :param order_by: Specifies the ordering of the output,
            defaults to ascending by timestamp.
        :param filter_: Limit output to events matching the specified Filter expression.
        :param limit: Limit output to a maximum number of events.
            Also determines the page size. Defaults to 2500.
        :param limit_by: Limit the combination of a specific set of Index fields
            to a specified maximum number.
        :param cursor: Specifies the next cursor,
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
        response = await self.http_post(self.EVENTS_URL,
                                        data={k: v for k, v in payload.items() if
                                              v is not None})
        if response.status_code != 200:
            self.log.warning(f"Unexpected status code: {response.status_code}")
            raise ObeliskError(response.status_code, response.reason_phrase)

        try:
            js = response.json()
            return QueryResult.model_vaidate(js)
        except json.JSONDecodeError as e:
            self.log.warning(f'Obelisk response is not a JSON object: {e}')
            raise ObeliskError
        except ValidationError as e:
            self.log.warning(f"Response cannot be validated: {e}")
            raise ObeliskError


async def query(self, datasets: List[str], metrics: List[str] | None = None,
                fields: dict | None = None,
                from_timestamp: int | None = None, to_timestamp: int | None = None,
                order_by: dict | None = None,
                filter_: dict | None = None,
                limit: int | None = None,
                limit_by: dict | None = None) -> List[Datapoint]:
    cursor: str | None | Literal[True] = True
    result_set: List[Datapoint] = []

    while cursor:
        actual_cursor = cursor if cursor is not True else None
        result: QueryResult = await self.single_chunk(datasets=datasets,
                                                      metrics=metrics, fields=fields,
                                                      from_timestamp=from_timestamp,
                                                      to_timestamp=to_timestamp,
                                                      order=order_by, filter_=filter_,
                                                      limit=limit,
                                                      limit_by=limit_by,
                                                      cursor=actual_cursor)
        result_set.extend(result.items)
        cursor = result.cursor

    return result_set


async def query_time_chunked(self, datasets: List[str], metrics: List[str],
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
        yield await self.query(datasets=datasets, metrics=metrics,
                               from_timestamp=current_start.timestamp(),
                               to_timestamp=(current_start + jump).timestamp() - 1,
                               order_by={"field": ["timestamp"], "ordering": direction},
                               filter_=filter_)
        current_start += jump
