"""
Obelisk-py is a client for the Obelisk data platform.
We support both "classic" Obelisk and HFS,
each with a synchronous and async API.
We also support Obelisk CORE, in async only for now.

The PyPi package name is `obelisk-py`, the Python module is called `obelisk`.

Your starting point will be one of the Obelisk instances in `.sync` or `.asynchronous` depending on your preferred API.

The Obelisk classes in these modules both implement the same interface,
but the asynchronous implementation returns Coroutines.

## Error handling

Obelisk-py comes with robust retry logic to handle any errors that may come up.
Issues like timeouts, temporary server errors or even DNS issues are fairly common, and handling them properly is important.
Each Client accepts a retry strategy of type `.strategies.retry.RetryStrategy`.
Several predefined strategies are available in `.strategies.retry`.

## Quick Start

Using CORE
```py
from obelisk.asynchronous.core import Client, QueryParams
from obelisk.types.core import Filter, Comparison
import os
import asyncio

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

# You may want to specify a retry strategy
client = Client(
    client=client_id,
    secret=client_secret
)

query = QueryParams(
    dataset="some-dataset",
    fields=["metric","labels","value","timestamp"],
    dataType="number",
    filter_=Filter().add_and(
        Comparison.equal("metric", "heart_rate::number"),
        Comparison.greater("timestamp", 42069180)
    )

data = asyncio.get_event_loop().run_until_complete(client.query(query))
```

Using Classic or HFS, synchronously (async is analogous)
```py
from obelisk.sync import Client
from obelisk.types import ObeliskKind
import os

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

# You may want to specify a retry strategy
client = Client(
    client=client_id,
    secret=client_secret,
    kind=ObeliskKind.CLASSIC # or HFS, as you wish
)

data = client.query(
    datasets=["some-dataset"],
    metrics=["heart-rate::number"],
    from_timestamp=42069180,
    filter_={
        "source": {
            "_startsWith": "user123"
        }
    }
)
```

## Changelog
.. include:: ../../CHANGELOG.rst
"""
