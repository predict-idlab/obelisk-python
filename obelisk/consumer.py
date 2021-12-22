"""Obelisk consumer."""

__author__ = 'Pieter Moens'
__email__ = 'Pieter.Moens@UGent.be'

import json
import requests
from sgqlc.operation import Operation
from sseclient import SSEClient

from obelisk.client import ObeliskClient, ObeliskException
from obelisk.schema import TimestampPrecision, Query, Mutation


class ObeliskConsumer(ObeliskClient):
    """
    Component that contains all the logic to consume data from
    the Obelisk API (e.g. historical data, sse).

    Obelisk API Documentation:
    https://obelisk.docs.apiary.io/
    """

    def __init__(self, client_id: str, client_secret: str, debug: bool = False):
        super().__init__(client_id, client_secret, debug)

    def events(self, datasets: list, metrics: list = None,
               precision: TimestampPrecision = TimestampPrecision.MILLISECONDS, fields: dict = None,
               from_timestamp: int = None, to_timestamp: int = None, order_by: dict = None, filter_: dict = None,
               limit: int = None, limit_by: dict = None, cursor: str = None):
        """
        Query historical events for the specified Metric.

        :param datasets: List of Dataset IDs.
        :param metrics: List of Metric IDs or wildcards (e.g. `*::number`).
        :param precision: Defines the timestamp precision for the returned results.
        :param fields: List of fields to return in the result set. Defaults to `[metric, source, value]`
        :param from_timestamp: Limit output to events after (and including) this UTC millisecond timestamp.
        :param to_timestamp: Limit output to events before (and excluding) this UTC millisecond timestamp.
        :param order_by: Specifies the ordering of the output, defaults to ascending by timestamp.
        :param filter_: Limit output to events matching the specified Filter expression.
        :param limit: Limit output to a maximum number of events. Also determines the page size. Defaults to 2500.
        :param limit_by: Limit the combination of a specific set of Index fields to a specified maximum number.
        :param cursor: Specifies the next cursor, used when paging through large result sets.
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
            'limitBy': limit_by,
            'timestampPrecision': precision
        }
        response = self.http_post(self.EVENTS_URL, data={k: v for k, v in payload.items() if v is not None})
        try:
            result = response.json()
            return result['items']
        except json.JSONDecodeError as e:
            self.logger.warning('Obelisk response is not a JSON object.')
            self.logger.warning('[%d]: %s', response.status_code, response.text)
            raise ObeliskException

    def get_active_stream(self, datasets: list, metrics: list = None,
                          precision: TimestampPrecision = TimestampPrecision.MILLISECONDS,
                          fields: list = None, filter_: dict = None) -> str or None:
        query = Operation(Query)
        query.me.activeStreams.items.id()
        query.me.activeStreams.items.dataRange()
        query.me.activeStreams.items.fields()
        query.me.activeStreams.items.timestampPrecision()
        query.me.activeStreams.items.filter()

        result = self.query_graphql(query)

        data_range = {
            'datasets': datasets
        }
        if metrics is not None:
            data_range['metrics'] = metrics

        input_ = {
            'dataRange': data_range,
            'timestampPrecision': precision
        }
        if fields is not None:
            input_['fields'] = fields
        if filter_ is not None:
            input_['filter'] = filter_

        active_streams = result['data']['me']['activeStreams']['items']
        for stream in active_streams:
            stream_ = stream.copy()
            stream_.pop('id')

            if stream_ == input_:
                return stream['id']

        return None

    def create_stream(self, name: str, datasets: list, metrics: list = None,
                      precision: TimestampPrecision = TimestampPrecision.MILLISECONDS,
                      fields: list = None, filter_: dict = None) -> str:
        """
        Create an event Stream for the Dataset.

        :param name: Name for the Stream.
        :param datasets: List of Dataset IDs for the Stream dataRange.
        :param metrics: List of Metric IDs or wildcards (e.g. `*::number`) for the Stream dataRange.
        :param precision: Defines the timestamp precision for the returned results.
        :param fields: List of fields to return in the result set. Defaults to `[metric, source, value]`
        :param filter_: Limit output to events matching the specified Filter expression.
        """
        active_stream = self.get_active_stream(datasets, metrics, precision, fields, filter_)
        if active_stream is not None:
            self.logger.info('Stream already exists, skipping creation..')
            return active_stream

        data_range = {
            'datasets': datasets
        }
        if metrics is not None:
            data_range['metrics'] = metrics

        input_ = {
            'name': name,
            'dataRange': data_range,
            'timestampPrecision': precision
        }
        if fields is not None:
            input_['fields'] = fields
        if filter_ is not None:
            input_['filter'] = filter_

        mutation = Operation(Mutation)
        mutation.createStream(input=input_)

        result = self.query_graphql(mutation)

        response_code = result['data']['createStream']['responseCode']
        message = result['data']['createStream']['message']
        if response_code != 'SUCCESS':
            raise ObeliskException(f'Could not create stream: [{response_code}] {message}')
        return result['data']['createStream']['item']['id']

    def sse(self, name: str = None, datasets: list = None, metrics: list = None, stream_id: int = None,
            receive_backlog: bool = False, **kwargs) -> (str, SSEClient):
        """
        Create and/or open an event Stream for the Dataset.
        If `stream_id` is not provided, a new stream will be created using the `name`, `datasets` and `metrics`.

        :param name: Name for the Stream.
        :param datasets: List of Dataset IDs for the Stream dataRange.
        :param metrics: List of Metric IDs or wildcards (e.g. `*::number`) for the Stream dataRange.
        :param stream_id: The id of the Stream.
        :param receive_backlog: Whether to receive events that were missed since last time the client was connected.
            If set to 'false' (default), Obelisk starts streaming live data immediately.
        :return: stream_id, SSEClient
        """
        self._verify_token()

        if stream_id is None:
            if name is None or datasets is None:
                raise ObeliskException('`name` or `datasets` not provided.')

            self.logger.info(f'Creating Stream for {{ datasets: {datasets}, metrics: {metrics} }}.')
            stream_id = self.create_stream(name, datasets, metrics, **kwargs)

        headers = {'Accept': 'text/event-stream', 'Authorization': f'Bearer {self.token}'}
        params = {
            'streamId': stream_id,
            'receiveBacklog': receive_backlog
        }
        self.logger.info(f'Connecting to Stream [{stream_id}] for {{ datasets: {datasets}, metrics: {metrics} }}.')
        response = requests.get(f'{self.STREAMS_URL}/{stream_id}', headers=headers, params=params, stream=True)
        return stream_id, SSEClient(response)
