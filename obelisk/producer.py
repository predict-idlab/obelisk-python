"""Obelisk producer."""

__author__ = 'Pieter Moens'
__email__ = 'Pieter.Moens@UGent.be'

from enum import Enum

from obelisk.client import ObeliskClient, ObeliskException
from obelisk.schema import TimestampPrecision


class IngestMode(Enum):
    DEFAULT = 'default'
    STREAM_ONLY = 'stream_only'
    STORE_ONLY = 'store_only'


class ObeliskProducer(ObeliskClient):
    """
    Component that contains all the logic to produce data to the Obelisk API.
    Obelisk API Documentation:
    https://obelisk.ilabt.imec.be/swagger/
    """
    def __init__(self, client_id, client_secret, debug: bool = False):
        super().__init__(client_id, client_secret, debug)

    def send(self, dataset: str, data, precision: TimestampPrecision = TimestampPrecision.MILLISECONDS,
             mode: IngestMode = IngestMode.DEFAULT):
        """
        Ingest data to Obelisk.

        :param dataset: The ID of the dataset to upload the events to.
        :param data: Array of data points (see Obelisk docs)
        :param precision: Determines how the UTC timestamps for the Metric Events should be interpreted.
        :param mode: mode of ingestion in Obelisk - can either be 'default' (data for both
                     storing and streaming), 'stream_only' or 'store_only'
        :return: requests.Response
        """
        params = {
            'datasetId': dataset,
            'timestampPrecision': precision,
            'mode': mode.value
        }

        response = self.http_post(f'{self.INGEST_URL}/{dataset}', data=data, params=params)
        if response.status_code != 204:
            self.logger.warning('An error occurred during data ingestion')
            self.logger.warning('[%d]: %s', response.status_code, response.text)
            raise ObeliskException
        return response.status_code
