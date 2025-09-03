from obelisk.asynchronous.base import BaseClient
from obelisk.exceptions import ObeliskError

from datetime import datetime, timedelta
import httpx
import json
from pydantic import BaseModel, AwareDatetime, ValidationError, model_validator
from typing import AsyncGenerator, Dict, Generator, Iterator, List, Literal, Optional, Any, get_args
from typing_extensions import Self
from numbers import Number


DataType = Literal['number', 'number[]', 'json', 'bool', 'string']


Aggregator = Literal['last', 'min', 'mean', 'max', 'count', 'stddev']


# https://obelisk.pages.ilabt.imec.be/obelisk-core/query.html#available-data-point-fields
FieldName = str # TODO: validate field names?


Datapoint = Dict[str, Any]


class ObeliskPosition(BaseModel):
    lat: float
    lng: float
    elevation: float


class IncomingDataPoint(BaseModel):
    timestamp: Optional[AwareDatetime] = None
    metric: str
    value: Any
    labels: Optional[Dict[str, str]] = None
    location: Optional[ObeliskPosition] = None

    @model_validator(mode='after')
    def check_metric_type(self) -> Self:
        split = self.metric.split('::')

        if len(split) != 2:
            raise ValueError("Incorrect amount of type qualifiers")

        suffix = split[1]
        if suffix not in get_args(DataType):
            raise ValueError(f"Invalid type suffix, should be one of {', '.join(get_args(DataType))}")

        if suffix == 'number' and not isinstance(self.value, Number):
            raise ValueError(f"Type suffix mismatch, expected number, got {type(self.value)}")

        if suffix == 'number[]':
            if type(self.value) is not list or any([not isinstance(x, Number) for x in self.value]):
                raise ValueError("Type suffix mismatch, expected value of number[]")

        # Do not check json, most things should be serialisable

        if suffix == 'bool' and type(self.value) is not bool:
            raise ValueError(f"Type suffix mismatch, expected bool, got {type(self.value)}")

        if suffix == 'string' and type(self.value) is not str:
            raise ValueError(f"Type suffix mismatch, expected bool, got {type(self.value)}")

        return self


class QueryParams(BaseModel):
    dataset: str
    groupBy: Optional[List[FieldName]] = None
    aggregator: Optional[Aggregator] = None
    fields: Optional[List[FieldName]] = None
    orderBy: Optional[List[str]] = None # More complex than just FieldName, can be prefixed with - to invert sort
    dataType: Optional[DataType] = None
    filter: Optional[str] = None # TODO: Validating this must be a nightmare
    cursor: Optional[str] = None
    limit: int = 1000

    @model_validator(mode='after')
    def check_datatype_needed(self) -> Self:
        if self.fields is None or 'value' in self.fields:
            if self.dataType is None:
                raise ValueError("Value field requested, must specify datatype")

        return self

    def to_dict(self) -> Dict:
        return self.model_dump(exclude_none=True)


class ChunkedParams(BaseModel):
    dataset: str
    metric: str
    groupBy: Optional[List[FieldName]] = None
    aggregator: Optional[Aggregator] = None
    fields: Optional[List[FieldName]] = None
    orderBy: Optional[List[str]] = None # More complex than just FieldName, can be prefixed with - to invert sort
    dataType: Optional[DataType] = None
    start: datetime
    end: datetime
    jump: timedelta = timedelta(hours=1)

    @model_validator(mode='after')
    def check_datatype_needed(self) -> Self:
        if self.fields is None or 'value' in self.fields:
            if self.dataType is None:
                raise ValueError("Value field requested, must specify datatype")

        return self

    def chunks(self) -> Iterator[QueryParams]:
        current_start = self.start
        while current_start < self.end:
            current_end = current_start + self.jump

            yield QueryParams(
                dataset=self.dataset,
                groupBy=self.groupBy,
                aggregator=self.aggregator,
                fields=self.fields,
                orderBy=self.orderBy,
                dataType=self.dataType,
                filter=f'timestamp>={current_start.isoformat()} and timestamp<{current_end.isoformat()} and metric=={self.metric}'
            )

            current_start += self.jump



class QueryResult(BaseModel):
    cursor: Optional[str] = None
    items: List[Datapoint]


class Core(BaseClient):
    page_limit: int = 250
    """How many datapoints to request per page in a cursored fetch"""

    async def send(
        self,
        dataset: str,
        data: List[IncomingDataPoint],
    ) -> httpx.Response:
        """
        Publishes data to Obelisk

        Parameters
        ----------
        dataset : str
            ID for the dataset to publish to
        data : List[IncomingDataPoint]
            List of Obelisk-acceptable datapoints.
            Exact format varies between Classic or HFS,
            caller is responsible for formatting.

        Raises
        ------

        ObeliskError
            When the resulting status code is not 204, an :exc:`~obelisk.exceptions.ObeliskError` is raised.
        """

        response = await self.http_post(
            f"{self._ingest_url}/{dataset}/data/ingest", data=[x.model_dump(mode='json') for x in data]
        )
        if response.status_code != 204:
            msg = f"An error occured during data ingest. Status {response.status_code}, message: {response.text}"
            self.log.warning(msg)
            raise ObeliskError(msg)
        return response

    async def fetch_single_chunk(
            self,
            params: QueryParams
    ) -> QueryResult:
        response = await self.http_get(
            f"{self._events_url}/{params.dataset}/data/query",
            params=params.to_dict()
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
            raise ObeliskError(msg)
        except ValidationError as e:
            msg = f"Response cannot be validated: {e}"
            self.log.warning(msg)
            raise ObeliskError(msg)

    async def query(
        self,
        params: QueryParams
    ) -> List[Datapoint]:
        params.cursor = None
        result_set: List[Datapoint] = []
        result_limit = params.limit

        # Obelisk CORE does not actually stop emitting a cursor when done, limit serves as page limit
        params.limit = self.page_limit

        while True:
            result: QueryResult = await self.fetch_single_chunk(
                params
            )
            result_set.extend(result.items)
            params.cursor = result.cursor

            if len(result_set) >= result_limit:
                break

        return result_set

    async def query_time_chunked(
        self,
        dataset: str,
        params: QueryParams,
        from_time: datetime,
        to_time: datetime,
        jump: timedelta,
        filter_: Optional[str] = None,
        direction: Literal["asc", "desc"] = "asc",
    ) -> AsyncGenerator[List[Datapoint], None]:
        raise NotImplementedError()
