from typing import List

import httpx

from construct_additional_obelisks.asynchronous.client import Client
from construct_additional_obelisks.exceptions import ObeliskError
from construct_additional_obelisks.types import IngestMode, TimestampPrecision


class Producer(Client):
    async def send(self, dataset: str, data: List[dict],
                   precision: TimestampPrecision = TimestampPrecision.MILLISECONDS,
                   mode: IngestMode = IngestMode.DEFAULT) -> httpx.Response:
        params = {
            'datasetId': dataset,
            'timestampPrecision': precision,
            'mode': mode.value
        }

        response = await self.http_post(f'{self.INGEST_URL}/{dataset}', data=data,
                                        params=params)
        if response.status_code != 204:
            self.log.warning('An error occurred during data ingestion')
            self.log.warning('[%d]: %s', response.status_code, response.text)
            raise ObeliskError
        return response
