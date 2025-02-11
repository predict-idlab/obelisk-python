from datetime import datetime
import logging

class Client:
    client: str = ""
    secret: str = ""

    token: str | None = None
    token_expires: datetime | None = None

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
