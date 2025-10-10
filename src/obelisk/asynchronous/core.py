"""
This module contains the asynchronous API to interface with Obelisk CORE.
These methods all return a :class:`Awaitable`.

Relevant entrance points are :class:`Client`.

This API vaguely resembles that of clients to previous Obelisk versions,
but also significantly diverts from it where the underlying Obelisk CORE API does so.
"""

from obelisk.asynchronous.base import BaseClient
from obelisk.exceptions import ObeliskError
from obelisk.types.core import FieldName, Filter

from datetime import datetime, timedelta
import httpx
import json
from pydantic import (
    BaseModel,
    AwareDatetime,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)
from typing import (
    Annotated,
    Literal,
    Any,
    cast,
    get_args,
)
from collections.abc import AsyncIterator, Iterator
from typing_extensions import Self
from numbers import Number

from obelisk.strategies.retry import NoRetryStrategy, RetryStrategy
from obelisk.types import ObeliskKind


DataType = Literal["number", "number[]", "json", "bool", "string"]
"""The possible types of data Obelisk can accept"""


def type_suffix(metric: str) -> DataType:
    """
    Extracts the :any:`DataType` from a string metric,
    useful for the dataType field in queries.

    Throws a :py:exc:`ValueError` if the provided string does not appear to be a typed metric,
    or the found type suffix is not a known one.
    """
    split = metric.split("::")

    if len(split) != 2:
        raise ValueError("Incorrect amount of type qualifiers")

    suffix = split[1]
    if suffix not in get_args(DataType):
        raise ValueError(
            f"Invalid type suffix, should be one of {', '.join(get_args(DataType))}"
        )
    return cast(DataType, suffix)


Aggregator = Literal["last", "min", "mean", "max", "count", "stddev"]
"""Type of aggregation Obelisk can process"""


Datapoint = dict[str, Any]
"""Datapoints resulting from queries are modeled as simple dicts, as fields can come and go depending on query."""


class ObeliskPosition(BaseModel):
    """
    Format for coordinates as expected by Obelisk.
    """

    lat: float
    """Latitude"""
    lng: float
    """Longitude"""
    elevation: float


class IncomingDatapoint(BaseModel):
    """A datapoint to be submitted to Obelisk. These are validated quite extensively, but not fully.
    .. automethod:: check_metric_type(self)
    """

    timestamp: AwareDatetime | None = None
    metric: str
    value: Any
    labels: dict[str, str] | None = None
    location: ObeliskPosition | None = None

    @model_validator(mode="after")
    def check_metric_type(self) -> Self:
        suffix = type_suffix(self.metric)

        if suffix == "number" and not isinstance(self.value, Number):
            raise ValueError(
                f"Type suffix mismatch, expected number, got {type(self.value)}"
            )

        if suffix == "number[]" and (
            type(self.value) is not list
            or any([not isinstance(x, Number) for x in self.value])
        ):
            raise ValueError("Type suffix mismatch, expected value of number[]")

        # Do not check json, most things should be serialisable

        if suffix == "bool" and type(self.value) is not bool:
            raise ValueError(
                f"Type suffix mismatch, expected bool, got {type(self.value)}"
            )

        if suffix == "string" and type(self.value) is not str:
            raise ValueError(
                f"Type suffix mismatch, expected bool, got {type(self.value)}"
            )

        return self


class QueryParams(BaseModel):
    dataset: str
    groupBy: list[FieldName] | None = None
    aggregator: Aggregator | None = None
    fields: list[FieldName] | None = None
    orderBy: list[str] | None = (
        None  # More complex than just FieldName, can be prefixed with - to invert sort
    )
    dataType: DataType | None = None
    filter_: Annotated[str | Filter | None, Field(serialization_alias="filter")] = None
    """
    Obelisk CORE handles filtering in `RSQL format <https://obelisk.pages.ilabt.imec.be/obelisk-core/query.html#rsql-format>`__ ,
    to make it easier to also programatically write these filters, we provide the :class:`Filter` option as well.

    Suffix to avoid collisions.
    """
    cursor: str | None = None
    limit: int = 1000

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def check_datatype_needed(self) -> Self:
        if (self.fields is None or "value" in self.fields) and self.dataType is None:
            raise ValueError("Value field requested, must specify datatype")

        return self

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True, by_alias=True)


class ChunkedParams(BaseModel):
    dataset: str
    groupBy: list[FieldName] | None = None
    aggregator: Aggregator | None = None
    fields: list[FieldName] | None = None
    orderBy: list[str] | None = (
        None  # More complex than just FieldName, can be prefixed with - to invert sort
    )
    dataType: DataType | None = None
    filter_: str | Filter | None = None
    """Underscore suffix to avoid name collisions"""
    start: datetime
    end: datetime
    jump: timedelta = timedelta(hours=1)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def check_datatype_needed(self) -> Self:
        if (self.fields is None or "value" in self.fields) and self.dataType is None:
            raise ValueError("Value field requested, must specify datatype")

        return self

    def chunks(self) -> Iterator[QueryParams]:
        current_start = self.start
        while current_start < self.end:
            current_end = current_start + self.jump
            filter_ = f"timestamp>={current_start.isoformat()};timestamp<{current_end.isoformat()}"
            if self.filter_:
                filter_ += f";{self.filter_}"

            yield QueryParams(
                dataset=self.dataset,
                groupBy=self.groupBy,
                aggregator=self.aggregator,
                fields=self.fields,
                orderBy=self.orderBy,
                dataType=self.dataType,
                filter_=filter_,
            )

            current_start += self.jump


class QueryResult(BaseModel):
    cursor: str | None = None
    items: list[Datapoint]


class Client(BaseClient):
    page_limit: int = 250
    """How many datapoints to request per page in a cursored fetch"""

    def __init__(
        self,
        client: str,
        secret: str,
        retry_strategy: RetryStrategy = NoRetryStrategy(),  # noqa: B008   # This is fine to bew shared
    ) -> None:
        BaseClient.__init__(
            self,
            client=client,
            secret=secret,
            retry_strategy=retry_strategy,
            kind=ObeliskKind.CORE,
        )

    async def send(
        self,
        dataset: str,
        data: list[IncomingDatapoint],
    ) -> httpx.Response:
        """
        Publishes data to Obelisk

        Parameters
        ----------
        dataset : str
            ID for the dataset to publish to
        data : List[IncomingDatapoint]
            List of Obelisk-acceptable datapoints.
            Exact format varies between Classic or HFS,
            caller is responsible for formatting.

        Raises
        ------

        ObeliskError
            When the resulting status code is not 204, an :exc:`~obelisk.exceptions.ObeliskError` is raised.
        """

        response = await self.http_post(
            f"{self.kind.root_url}/{dataset}/data/ingest",
            data=[x.model_dump(mode="json") for x in data],
        )
        if response.status_code != 204:
            msg = f"An error occured during data ingest. Status {response.status_code}, message: {response.text}"
            self.log.warning(msg)
            raise ObeliskError(msg)
        return response

    async def fetch_single_chunk(self, params: QueryParams) -> QueryResult:
        response = await self.http_get(
            f"{self.kind.root_url}/{params.dataset}/data/query", params=params.to_dict()
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

    async def query(self, params: QueryParams) -> list[Datapoint]:
        params.cursor = None
        result_set: list[Datapoint] = []
        result_limit = params.limit

        # Obelisk CORE does not actually stop emitting a cursor when done, limit serves as page limit
        params.limit = self.page_limit

        while True:
            result: QueryResult = await self.fetch_single_chunk(params)
            result_set.extend(result.items)
            params.cursor = result.cursor

            if len(result_set) >= result_limit or result.cursor is None:
                break

        return result_set

    async def query_time_chunked(
        self, params: ChunkedParams
    ) -> AsyncIterator[list[Datapoint]]:
        for chunk in params.chunks():
            yield await self.query(chunk)
