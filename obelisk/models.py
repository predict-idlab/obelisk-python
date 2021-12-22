from enum import Enum
from sgqlc.types import ArgDict, Boolean, Field, Int, String, Type, list_of, non_null
from sgqlc.types.relay import Node


page_args = ArgDict({
    'cursor': String,
    'limit': Int
})


class Page(Type):
    cursor = String
    count = Int


class Metric(Node):
    id = String

    things = Field('ThingPage')


class Thing(Node):
    id = String

    metrics = Field('MetricPage')


class Dataset(Node):
    id = String
    name = String
    description = String

    metric = Field(Metric, args=ArgDict({'id': String}))
    metrics = Field('MetricPage', args=page_args)

    thing = Field(Thing, args=ArgDict({'id': String}))
    things = Field('ThingPage', args=page_args)


class MetricPage(Page):
    items = Field(Metric)


class ThingPage(Page):
    items = Field(Thing)


class DatasetPage(Page):
    items = Field(Dataset)


class DataRange(Type):
    datasets = Field(Dataset)
    metrics = String


class DataStream(Node):
    id = String
    name = String
    dataRange = Field(DataRange)
    clientConnected = Boolean


class DataStreamPage(Page):
    items = Field(DataStream)


class User(Node):
    id = String
    email = String

    dataset = Field(Dataset, args=ArgDict({'id': String}))
    datasets = Field(DatasetPage, args=page_args)

    activeStream = Field(DataStream, args=ArgDict({'id': String}))
    activeStreams = Field(DataStreamPage, args=page_args)


class Query(Type):
    me = Field(User)


class IngestMode(Enum):
    DEFAULT = 'default'
    STREAM_ONLY = 'stream_only'
    STORE_ONLY = 'store_only'


class EventField(Enum):
    TIMESTAMP = 'timestamp'
    DATASET = 'dataset'
    METRIC = 'metric'
    PRODUCER = 'producer'
    SOURCE = 'source'
    VALUE = 'value'
    TAGS = 'tags'
    LOCATION = 'location'
    GEOHASH = 'geohash'
    ELEVATION = 'elevation'
    TS_RECEIVED = 'tsReceived'

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))


class TimestampPrecision(Enum):
    SECONDS = 'seconds'
    MILLISECONDS = 'milliseconds'
    MICROSECONDS = 'microseconds'


class CreateStreamInput:

    def __init__(self, name, datasets, metrics: list = None,
                 precision: TimestampPrecision = TimestampPrecision.MILLISECONDS,
                 fields: list = None, filter_: dict = None):
        self.name = name
        self.data_range = DataRange(datasets, metrics)
        self.precision = precision
        self.fields = fields
        self.filter = filter_

    def __str__(self):
        output_ = f'{{ name: "{ self.name }" dataRange: { self.data_range } ' \
                  f'timestampPrecision: { self.precision.value.upper() }'

        if self.fields is not None:
            output_ += f' fields: { [field.value.upper() for field in self.fields] }'.replace("'", '')
        if self.filter is not None:
            output_ += f' filter: { self.filter }'

        output_ += ' }'
        return output_.replace("'", '"')
