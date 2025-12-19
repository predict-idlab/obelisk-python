"""
This module contains the asynchronous API to interface with Obelisk CORE.
These methods all return a `Awaitable`.

Relevant entrance points are `Client`.

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
    SerializerFunctionWrapHandler,
    WrapSerializer,
    field_serializer,
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
from obelisk.types.core import IngestMode


DataType = Literal["number", "number[]", "json", "bool", "string", "integer", "integer[]"]
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
    We check roughly if the value type corresponds to the declared type if its one of `number`, `number[]`, `bool` or `string`.
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

        if suffix == "integer" and not isinstance(self.value, int):
            raise ValueError("Type suffix mismatch, expected value of type integer")

        if suffix == "integer[]" and (
            type(self.value) is not list
            or any([not isinstance(x, int) for x in self.value])
        ):
            raise ValueError("Type suffix mismatch, expected value of integer[]")

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


def serialize_comma_string(
    input: Any, handler: SerializerFunctionWrapHandler
) -> str | None:
    if val := handler(input):
        return ",".join(val)
    return None


class QueryParams(BaseModel):
    """
    To avoid having too many parameters on query functions,
    and sharing the implementation between query and chunked query,
    this model collects the information needed to execute a query.

    Contrary to the name, this does not correlate directly to URL query parameters sent to Obelisk.
    """

    dataset: str
    groupBy: Annotated[
        list[FieldName] | None, WrapSerializer(serialize_comma_string)
    ] = None
    """List of Field Names to aggregate by as defined in Obelisk docs, None selects the server-side defaults."""
    aggregator: Aggregator | None = None
    fields: Annotated[
        list[FieldName] | None, WrapSerializer(serialize_comma_string)
    ] = None
    """List of Field Names as defined in Obelisk docs, None selects the server-side defaults."""
    orderBy: Annotated[list[str] | None, WrapSerializer(serialize_comma_string)] = None
    """List of Field Names, with their potential prefixes and suffixes, to select ordering. None user server defaults."""
    dataType: DataType | None = None
    """Data type expected to be returned, is mandatory if the `value` field is requested in the `fields` parameter"""
    filter_: Annotated[str | Filter | None, Field(serialization_alias="filter",)] = None
    """
    Obelisk CORE handles filtering in [RSQL format](https://obelisk.pages.ilabt.imec.be/obelisk-core/query.html#rsql-format),
    to make it easier to also programatically write these filters, we provide the `obelisk.types.core.Filter` option as well.

    Suffix to avoid collisions with builtin Python filter function.
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
        return self.model_dump(
            exclude_none=True, by_alias=True, mode="json", exclude={"dataset"}
        )

    @field_serializer('filter_', mode='plain')
    def serialize_filter(self, value: Filter | str | None) -> str | None:
        if value is None or isinstance(value, str):
            return value

        return str(value)


class ChunkedParams(BaseModel):
    """
    The parameters to be used with `Client.query_time_chunked`,
    which allows fetching large spans of data in specified "chunks" specified in time units,
    for example processing weeks of data one hour at a time.
    This limits memory useage.
    """

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
    """The size of one chunk. 1 hour is a common default. You will receive however many datapoints are included in this interval."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def check_datatype_needed(self) -> Self:
        if (self.fields is None or "value" in self.fields) and self.dataType is None:
            raise ValueError("Value field requested, must specify datatype")

        return self

    def chunks(self) -> Iterator[QueryParams]:
        """Splits this model into an Iterator of ordinary `QueryParams` objects, to query one timestep at a time."""
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
    """The data returned by a single chunk fetch"""

    cursor: str | None = None
    """Cursors always point to the next page of data matched by filters.
    They are none if there is no more data, they do not consider datapoint count limits."""
    items: list[Datapoint]


class Client(BaseClient):
    """
    This class performs all communication with Obelisk.

    The intended methods to be used by consumers are `query` or `query_time_chunked`.
    These will respectively return all data matching specified parameters,
    or return all data, one timestep at a time respectively.

    `send` is considered an implementation detail,
    but may be used by consumers for any endpoints not yet implemented by obelisk-py.

    `fetch_single_chunk` is the underlying layer to both query methods and requires the user to handle cursors themselves.
    It may however still be useful in some circumstances.
    """

    page_limit: int = 250
    """How many datapoints to request per page in a cursored fetch"""

    def __init__(
        self,
        client: str,
        secret: str,
        retry_strategy: RetryStrategy = NoRetryStrategy(),  # noqa: B008   # This is fine to be shared
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
        ingest_mode: IngestMode = IngestMode.BOTH,
    ) -> httpx.Response:
        """
        Publishes data to Obelisk

        Parameters
        ----------
        - dataset
            ID for the dataset to publish to
        - data
            List of Obelisk-acceptable datapoints.
            Exact format varies between Classic or HFS,
            caller is responsible for formatting.

        Raises
        ------

        - ObeliskError
            When the resulting status code is not 204, an `obelisk.exceptions.ObeliskError` is raised.
        """

        response = await self.http_post(
            f"{self.kind.root_url}/{dataset}/data/ingest",
            data=[x.model_dump(mode="json") for x in data],
            params={"mode": ingest_mode.value}
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

        while True:
            params.limit = min(self.page_limit, result_limit - len(result_set))
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
