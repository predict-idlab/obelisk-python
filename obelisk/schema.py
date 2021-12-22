import json
from sgqlc.types import ArgDict, Boolean, Enum, Field, Input, Int, list_of, non_null, Scalar, String, Type, ODict, Variable
from sgqlc.types.relay import Node


page_args = ArgDict({
    'cursor': String,
    'limit': Int
})


class JSON(Scalar):

    converter = dict

    @classmethod
    def __to_graphql_input__(cls, value, indent=0, indent_string='  '):
        args = []
        if isinstance(value, dict):
            for key, value in value.items():
                args_value = cls.__to_graphql_input__(value, indent=indent, indent_string=indent_string)
                args.append(f'{key}: {args_value}')
        else:
            if isinstance(value, str):
                value = f'"{value}"'
            return value

        return '{' + ', '.join(args) + '}'


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


class TimestampPrecision(Enum):
    __choices__ = ('SECONDS', 'MILLISECONDS', 'MICROSECONDS')

    SECONDS = 'seconds'
    MILLISECONDS = 'milliseconds'
    MICROSECONDS = 'microseconds'


class EventField(Enum):
    __choices__ = ('timestamp', 'dataset', 'metric', 'producer', 'source', 'value', 'tags', 'location', 'geohash',
                   'elevation', 'tsReceived')

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


class DataStream(Node):
    id = String
    name = String
    dataRange = Field(DataRange)
    timestampPrecision = TimestampPrecision
    fields = list_of(EventField)
    filter = JSON
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


class DataRangeInput(Input):
    datasets = list_of(String)
    metrics = list_of(String)


class CreateStreamInput(Input):
    name = String
    dataRange = DataRangeInput
    timestampPrecision = TimestampPrecision
    fields = list_of(EventField)
    filter = JSON


class CreateStream(Type):
    responseCode = String
    message = String
    item = Field(DataStream)


class Mutation(Type):
    createStream = Field(CreateStream, args=ArgDict({'input': CreateStreamInput}))
