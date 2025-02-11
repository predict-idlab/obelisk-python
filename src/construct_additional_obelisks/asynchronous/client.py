from datetime import datetime, timedelta
import logging
import base64
from typing import Any

import httpx

from src.construct_additional_obelisks.exceptions import AuthenticationError
from src.construct_additional_obelisks.strategies.retry import RetryStrategy, \
    NoRetryStrategy
from src.construct_additional_obelisks.types import ObeliskKind


class Client:
    client: str = ""
    secret: str = ""

    token: str | None = None
    token_expires: datetime | None = None

    grace_period: timedelta = timedelta(seconds=10)
    retry_strategy: RetryStrategy
    kind: ObeliskKind

    log: logging.Logger

    TOKEN_URL = 'https://obelisk.ilabt.imec.be/api/v3/auth/token'
    ROOT_URL = 'https://obelisk.ilabt.imec.be/api/v3'
    METADATA_URL = 'https://obelisk.ilabt.imec.be/api/v3/catalog/graphql'
    EVENTS_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/query/events'
    INGEST_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/ingest'
    STREAMS_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/streams'

    def __init__(self, client: str, secret: str,
                 retry_strategy: RetryStrategy = NoRetryStrategy(),
                 kind: ObeliskKind = ObeliskKind.CLASSIC) -> None:
        self.client = client
        self.secret = secret
        self.retry_strategy = retry_strategy
        self.kind = kind

        self.log = logging.getLogger('obelisk')

        if self.kind == ObeliskKind.HFS:
            self.TOKEN_URL = 'https://obelisk-hfs.discover.ilabt.imec.be/auth/realms/obelisk-hfs/protocol/openid-connect/token'
            self.ROOT_URL = 'https://obelisk-hfs.discover.ilabt.imec.be'
            self.EVENTS_URL = 'https://obelisk-hfs.discover.ilabt.imec.be/data/query/events'
            self.INGEST_URL = 'https://obelisk-hfs.discover.ilabt.imec.be/data/ingest'
        else:
            self.TOKEN_URL = 'https://obelisk.ilabt.imec.be/api/v3/auth/token'
            self.ROOT_URL = 'https://obelisk.ilabt.imec.be/api/v3'
            self.METADATA_URL = 'https://obelisk.ilabt.imec.be/api/v3/catalog/graphql'
            self.EVENTS_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/query/events'
            self.INGEST_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/ingest'
            self.STREAMS_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/streams'

    async def _get_token(self):
        auth_string = str(base64.b64encode(
            f'{self.client}:{self.secret}'.encode('utf-8')), 'utf-8')
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': ('application/x-www-form-urlencoded'
                             if self.kind == ObeliskKind.HFS else 'application/json')
        }
        payload = {
            'grant_type': 'client_credentials'
        }

        async with httpx.AsyncClient() as client:
            request = await client.post(
                self.TOKEN_URL,
                json=payload if self.kind == ObeliskKind.CLASSIC else None,
                data=payload if self.kind == ObeliskKind.HFS else None,
                headers=headers)

            response = request.json()

            if request.status_code != 200:
                if 'error' in response:
                    self.log.warning(f"Could not authenticate, {response['error']}")
                    raise AuthenticationError

            self.token = response['access_token']
            self.token_expires = (datetime.now()
                                  + timedelta(seconds=response['expires_in']))

    async def _verify_token(self):
        if (self.token is None
                or self.token_expires < (datetime.now() - self.grace_period)):
            await self._get_token()

    async def http_post(self, url: str, data: Any = None,
                        params: dict | None = None) -> httpx.Response:
        await self._verify_token()

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        if params is None:
            params = {}
        async with httpx.AsyncClient() as client:
            response = None
            retry = self.retry_strategy.make()
            while not response or await retry.should_retry():
                if response is not None:
                    self.log.debug(f"Retrying, last response: {response.status_code}")

                response = await client.post(url,
                                             json=data,
                                             params={k: v for k, v in params.items() if
                                                     v is not None},
                                             headers=headers)

                if response.status_code // 100 == 2:
                    return response
            return response
