from typing import List

import httpx

from construct_additional_obelisks.asynchronous.client import Client
from construct_additional_obelisks.exceptions import ObeliskError
from construct_additional_obelisks.types import IngestMode, TimestampPrecision


class Producer(Client):
    """
    Allows publishing of data to Obelisk.
    """

    async def send(self, dataset: str, data: List[dict],
                   precision: TimestampPrecision = TimestampPrecision.MILLISECONDS,
                   mode: IngestMode = IngestMode.DEFAULT) -> httpx.Response:
        """
        Publishes data to Obelisk

        Parameters
        ----------
        dataset : str
            ID for the dataset to publish to
        data : List[dict]
            List of Obelisk-acceptable datapoints.
            Exact format varies between Classic or HFS,
            caller is responsible for formatting.
        precision : :class:`~construct_additional_obelisks.types.TimestampPrecision` = TimestampPrecision.MILLISECONDS
            Precision used in the numeric timestamps contained in data.
            Ensure it matches to avoid weird errors.
        mode : :class:`~construct_additional_obelisks.types.IngestMode` = IngestMode.DEFAULT
            See docs for :class:`~construct_additional_obelisks.types.IngestMode`.

        Raises
        ------

        ObeliskError
            When the resulting status code is not 204, an empty :exc:`~construct_additional_obelisks.exceptions.ObeliskError` is raised.
        """

        params = {
            'datasetId': dataset,
            'timestampPrecision': precision,
            'mode': mode.value
        }

        response = await self.http_post(f'{self._ingest_url}/{dataset}', data=data,
                                        params=params)
        if response.status_code != 204:
            self.log.warning('An error occurred during data ingestion')
            self.log.warning('[%d]: %s', response.status_code, response.text)
            raise ObeliskError
        return response
