from datetime import datetime, timedelta
import logging
import base64
from typing import Any, Optional

import httpx

from obelisk.exceptions import AuthenticationError
from obelisk.strategies.retry import RetryStrategy, \
    NoRetryStrategy
from obelisk.types import ObeliskKind


class Client:
    """
    Base class handling Obelisk auth and doing the core HTTP communication.
    Only exists in asynchronous variety, as it is not usually directly useful for user code.
    """

    _client: str = ""
    _secret: str = ""

    token: Optional[str] = None
    """Current authentication token"""
    token_expires: Optional[datetime] = None
    """Deadline after which token is no longer useable"""

    grace_period: timedelta = timedelta(seconds=10)
    """Controls how much before the expiration deadline a token will be refreshed."""
    retry_strategy: RetryStrategy
    kind: ObeliskKind

    log: logging.Logger

    _token_url = 'https://obelisk.ilabt.imec.be/api/v3/auth/token'
    _root_url = 'https://obelisk.ilabt.imec.be/api/v3'
    _metadata_url = 'https://obelisk.ilabt.imec.be/api/v3/catalog/graphql'
    _events_url = 'https://obelisk.ilabt.imec.be/api/v3/data/query/events'
    _ingest_url = 'https://obelisk.ilabt.imec.be/api/v3/data/ingest'
    _streams_url = 'https://obelisk.ilabt.imec.be/api/v3/data/streams'

    def __init__(self, client: str, secret: str,
                 retry_strategy: RetryStrategy = NoRetryStrategy(),
                 kind: ObeliskKind = ObeliskKind.CLASSIC) -> None:
        self._client = client
        self._secret = secret
        self.retry_strategy = retry_strategy
        self.kind = kind

        self.log = logging.getLogger('obelisk')

        if self.kind == ObeliskKind.HFS:
            self._token_url = 'https://obelisk-hfs.discover.ilabt.imec.be/auth/realms/obelisk-hfs/protocol/openid-connect/token'
            self._root_url = 'https://obelisk-hfs.discover.ilabt.imec.be'
            self._events_url = 'https://obelisk-hfs.discover.ilabt.imec.be/data/query/events'
            self._ingest_url = 'https://obelisk-hfs.discover.ilabt.imec.be/data/ingest'
        else:
            self._token_url = 'https://obelisk.ilabt.imec.be/api/v3/auth/token'
            self._root_url = 'https://obelisk.ilabt.imec.be/api/v3'
            self._metadata_url = 'https://obelisk.ilabt.imec.be/api/v3/catalog/graphql'
            self._events_url = 'https://obelisk.ilabt.imec.be/api/v3/data/query/events'
            self._ingest_url = 'https://obelisk.ilabt.imec.be/api/v3/data/ingest'
            self._streams_url = 'https://obelisk.ilabt.imec.be/api/v3/data/streams'

    async def _get_token(self):
        auth_string = str(base64.b64encode(
            f'{self._client}:{self._secret}'.encode('utf-8')), 'utf-8')
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': ('application/x-www-form-urlencoded'
                             if self.kind == ObeliskKind.HFS else 'application/json')
        }
        payload = {
            'grant_type': 'client_credentials'
        }

        async with httpx.AsyncClient() as client:
            response = None
            last_error = None
            retry = self.retry_strategy.make()
            while not response or await retry.should_retry():
                try:
                    request = await client.post(
                        self._token_url,
                        json=payload if self.kind == ObeliskKind.CLASSIC else None,
                        data=payload if self.kind == ObeliskKind.HFS else None,
                        headers=headers)

                    response = request.json()
                except Exception as e:
                    last_error = e
                    self.log.error(e)
                    continue

            if response is None and last_error is not None:
                raise last_error

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
            retry = self.retry_strategy.make()
            first = True
            while first or await retry.should_retry():
                first = False
                try:
                    await self._get_token()
                    return
                except:
                    continue

    async def http_post(self, url: str, data: Any = None,
                        params: Optional[dict] = None) -> httpx.Response:
        """
        Send an HTTP POST request to Obelisk,
        with proper auth.

        Possibly refreshes the authentication token and performs backoff as per `retry_strategy`.
        This method is not of stable latency because of these properties.

        No validation is performed on the input data,
        callers are responsible for formatting it in a method Obelisk understands.
        """

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
            last_error = None
            while not response or await retry.should_retry():
                if response is not None:
                    self.log.debug(f"Retrying, last response: {response.status_code}")

                try:
                    response = await client.post(url,
                                                 json=data,
                                                 params={k: v for k, v in params.items() if
                                                         v is not None},
                                                 headers=headers)

                    if response.status_code // 100 == 2:
                        return response
                except Exception as e:
                    self.log.error(e)
                    last_error = e
                    continue

            if not response and last_error:
                raise last_error
            return response
