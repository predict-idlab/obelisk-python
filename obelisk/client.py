"""Obelisk client."""

__author__ = 'Pieter Moens'
__email__ = 'Pieter.Moens@UGent.be'

import base64
from datetime import datetime, timedelta
import logging
import requests
from sgqlc.endpoint.http import HTTPEndpoint
from sgqlc.operation import Operation

from obelisk.schema import Query


class ObeliskException(Exception):
    pass


class ObeliskClient:
    """
    Component that contains all the logic to access the Obelisk API (e.g. Authentication).
    Obelisk Documentation:
    https://obelisk.ilabt.imec.be/docs/guides/auth.html
    """
    TOKEN_URL = 'https://obelisk.ilabt.imec.be/api/v3/auth/token'
    ROOT_URL = 'https://obelisk.ilabt.imec.be/api/v3'
    METADATA_URL = 'https://obelisk.ilabt.imec.be/api/v3/catalog/graphql'
    EVENTS_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/query/events'
    INGEST_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/ingest'
    STREAMS_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/streams'

    def __init__(self, client_id: str, client_secret: str, debug: bool = False):
        """
        Initialize the object.

        :param client_id: Obelisk client ID
        :param client_secret: Obelisk client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret

        self.token = None
        self.token_expires = None

        self._verify_token()

        self.logger = logging.getLogger('obelisk-python')
        if debug:
            self.logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()

        formatter = logging.Formatter('[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    # AUTHENTICATION FLOW
    def _get_token(self):
        """Get an access token from Obelisk."""
        auth_string = str(base64.b64encode(
            f'{self.client_id}:{self.client_secret}'.encode('utf-8')), 'utf-8')
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json'
        }
        payload = {
            'grant_type': 'client_credentials'
        }

        with requests.post(self.TOKEN_URL, json=payload, headers=headers) as req:
            response = req.json()

            if req.status_code != 200:
                if 'error' in response:
                    logging.warning('An error occurred during authentication with Obelisk')
                    logging.warning('Description: %s', response['error']['message'])
                    raise ObeliskException

            self.token = response['token']
            self.token_expires = datetime.now() + timedelta(seconds=response['max_valid_time'])

    def _verify_token(self):
        """Verify token from Obelisk."""
        if self.token is None or self.token_expires < datetime.now():
            self._get_token()

    def http_post(self, url: str, data: dict = None, params: dict = None) -> requests.Response:
        """
        Execute HTTP POST request on an API endpoint.

        :param url: API endpoint
        :param data: Payload as dictionary
        :param params: Parameters as dictionary
        """
        self._verify_token()

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        if params is None:
            params = {}
        with requests.post(url,
                           json=data,
                           params={k: v for k, v in params.items() if v is not None},
                           headers=headers) as response:
            return response

    # METADATA
    def query_graphql(self, query):
        """
        Retrieve metadata through GraphQL endpoints.

        :param query: GraphQL query (sgqlc.operation.Operation or str)
        :return: Query result as JSON object
        """
        self._verify_token()

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        endpoint = HTTPEndpoint(url=self.METADATA_URL, base_headers=headers)
        return endpoint(query=query)

    def get_datasets(self, cursor: str = None,
                     limit: int = None, filter_=None) -> []:
        """
        List datasets the current user/client has access to.

        :param cursor: The pagination cursor from which results should be listed for the resource.
        :param limit: Limits the number of returned results in the response page.
        :param filter_: Allows filtering instances of Dataset
            based on a number of predefined searchable fields (see Obelisk documentation).
        :return: List of datasets
        """
        query = Operation(Query)

        args = {
            'cursor': cursor,
            'limit': limit,
            'filter': filter_
        }
        query.me.datasets(**{k: v for k, v in args.items() if v is not None})

        result = self.query_graphql(query)

        return result['data']['me']['datasets']

    def get_dataset(self, dataset: str):
        """
        Retrieves a specific dataset.

        :param dataset: ID of the Dataset
        :return: Dataset
        """
        query = Operation(Query)
        dataset = query.me.dataset(id=dataset)
        dataset.id()
        dataset.name()
        dataset.description()

        result = self.query_graphql(query)

        return result['data']['me']['dataset']

    def get_metrics(self, dataset: str, cursor: str = None,
                    limit: int = None, filter_=None) -> dict:
        """
        Retrieve available metrics for a scope.

        :param dataset: The id of the Dataset.
        :param cursor: The pagination cursor from which results should be listed for the resource.
        :param limit: Limits the number of returned results in the response page.
        :param filter_: Allows filtering instances of Metric
            based on a number of predefined searchable fields (see Obelisk documentation).
        """
        query = Operation(Query)
        dataset = query.me.dataset(id=dataset)

        args = {
            'cursor': cursor,
            'limit': limit,
            'filter': filter_
        }
        dataset.metrics(**{k: v for k, v in args.items() if v is not None})

        result = self.query_graphql(query)
        return result['data']['me']['dataset']['metrics']

    def get_metric(self, dataset: str, metric: str) -> dict:
        """
        Get a specific Metric.

        :param dataset: The id of the Dataset.
        :param metric: The id of the Metric.
        """
        query = Operation(Query)
        dataset = query.me.dataset(id=dataset)
        dataset.metric(id=metric)

        result = self.query_graphql(query)
        return result['data']['me']['dataset']['metric']

    def get_things(self, dataset: str, cursor: str = None,
                   limit: int = None, filter_=None) -> dict:
        """
        Retrieve available metrics for a scope.

        :param dataset: The id of the Dataset.
        :param cursor: The pagination cursor from which results should be listed for the resource.
        :param limit: Limits the number of returned results in the response page.
        :param filter_: Allows filtering instances of Metric
            based on a number of predefined searchable fields (see Obelisk documentation).
        """
        query = Operation(Query)
        dataset = query.me.dataset(id=dataset)

        args = {
            'cursor': cursor,
            'limit': limit,
            'filter': filter_
        }
        dataset.things(**{k: v for k, v in args.items() if v is not None})

        result = self.query_graphql(query)
        return result['data']['me']['dataset']['things']

    def get_thing(self, dataset: str, thing: str) -> dict:
        """
        Get a specific Thing.

        :param dataset: The id of the Dataset.
        :param thing: The id of the Thing.
        """
        query = Operation(Query)
        dataset = query.me.dataset(id=dataset)
        dataset.thing(id=thing)

        result = self.query_graphql(query)
        return result['data']['me']['dataset']['thing']
