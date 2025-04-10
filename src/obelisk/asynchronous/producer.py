from typing import List

import httpx

from obelisk.asynchronous.client import Client
from obelisk.exceptions import ObeliskError
from obelisk.types import IngestMode, TimestampPrecision


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
        precision : :class:`~obelisk.types.TimestampPrecision` = TimestampPrecision.MILLISECONDS
            Precision used in the numeric timestamps contained in data.
            Ensure it matches to avoid weird errors.
        mode : :class:`~obelisk.types.IngestMode` = IngestMode.DEFAULT
            See docs for :class:`~obelisk.types.IngestMode`.

        Raises
        ------

        ObeliskError
            When the resulting status code is not 204, an empty :exc:`~obelisk.exceptions.ObeliskError` is raised.
        """

        params = {
            'datasetId': dataset,
            'timestampPrecision': precision.value,
            'mode': mode.value
        }

        response = await self.http_post(f'{self._ingest_url}/{dataset}', data=data,
                                        params=params)
        if response.status_code != 204:
            msg = f'An error occured during data ingest. Status {response.status_code}, message: {response.text}'
            self.log.warning(msg)
            raise ObeliskError(msg)
        return response
