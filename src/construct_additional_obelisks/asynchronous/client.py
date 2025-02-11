from datetime import datetime, timedelta
import logging
import base64
from typing import Any

import httpx

from src.construct_additional_obelisks.exceptions import AuthenticationError


class Client:
    client: str = ""
    secret: str = ""

    token: str | None = None
    token_expires: datetime | None = None

    grace_period: timedelta = timedelta(seconds=10)

    log: logging.Logger

    TOKEN_URL = 'https://obelisk.ilabt.imec.be/api/v3/auth/token'
    ROOT_URL = 'https://obelisk.ilabt.imec.be/api/v3'
    METADATA_URL = 'https://obelisk.ilabt.imec.be/api/v3/catalog/graphql'
    EVENTS_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/query/events'
    INGEST_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/ingest'
    STREAMS_URL = 'https://obelisk.ilabt.imec.be/api/v3/data/streams'

    def __init__(self, client: str, secret: str):
        self.client = client
        self.secret = secret

        self.log = logging.getLogger('obelisk')

    async def _get_token(self):
        auth_string = str(base64.b64encode(
            f'{self.client}:{self.secret}'.encode('utf-8')), 'utf-8')
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json'
        }
        payload = {
            'grant_type': 'client_credentials'
        }

        async with httpx.AsyncClient() as client:
            request = await client.post(self.TOKEN_URL, json=payload, headers=headers)

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
                        params: dict = None) -> httpx.Response:
        await self._verify_token()

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        if params is None:
            params = {}
        async with httpx.AsyncClient() as client:
            response = await client.post(url,
                                         json=data,
                                         params={k: v for k, v in params.items() if
                                                 v is not None},
                                         headers=headers)
            if response.status_code != 401:
                return response

            # Refresh token and retry _once_
            await self._verify_token()
            return await client.post(url,
                                     json=data,
                                     params={k: v for k, v in params.items() if
                                             v is not None},
                                     headers=headers)
