from enum import Enum
from typing import List, Any, Optional

from pydantic import BaseModel


class IngestMode(str, Enum):
    """
    Classic Obelisk accepts three ways of submitting new data.
    This integrates with the concept of Streams,
    which is a way to process datapoints as they come in.

    The default submission method is to publish both to long-term storage
    and stream.
    This IngestMode can be changed to change this default.

    Does not apply to HFS
    """

    DEFAULT = 'default'
    STREAM_ONLY = 'stream_only'
    STORE_ONLY = 'store_only'


class TimestampPrecision(str, Enum):
    """
    When ingesting data it is important to specify which precision provided UNIX timestamps are in.
    If a provided timestamp is in seconds,
    but interpreted by Obelisk as milliseconds, it would erroneously be somewhere in the past.
    """

    __choices__ = ('SECONDS', 'MILLISECONDS', 'MICROSECONDS')

    SECONDS = 'seconds'
    MILLISECONDS = 'milliseconds'
    MICROSECONDS = 'microseconds'


class Datapoint(BaseModel, extra='allow'):
    timestamp: int
    value: Any
    dataset: Optional[str] = None
    metric: Optional[str] = None
    source: Optional[str] = None
    userId: Optional[int] = None  # Only if HFS and no other name for field


class QueryResult(BaseModel):
    items: List[Datapoint]
    cursor: Optional[str] = None


class ObeliskKind(str, Enum):
    CLASSIC = 'classic'
    HFS = 'hfs'
