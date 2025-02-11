from enum import Enum
from typing import List, Any

from pydantic import BaseModel


class IngestMode(Enum):
    DEFAULT = 'default'
    STREAM_ONLY = 'stream_only'
    STORE_ONLY = 'store_only'


class TimestampPrecision(Enum):
    __choices__ = ('SECONDS', 'MILLISECONDS', 'MICROSECONDS')

    SECONDS = 'seconds'
    MILLISECONDS = 'milliseconds'
    MICROSECONDS = 'microseconds'


class Datapoint(BaseModel, extra='allow'):
    timestamp: int
    value: Any
    dataset: str | None = None
    metric: str | None = None
    source: str | None = None
    userId: int | None = None # Only if HFS and no other name for field


class QueryResult(BaseModel):
    items: List[Datapoint]
    cursor: str | None = None


class ObeliskKind(Enum):
    CLASSIC = 'classic'
    HFS = 'hfs'