import pytest
from obelisk.asynchronous import Obelisk

# Intentionally public client, restricted to public datasets.
client_id = "682c6c46604b3b3be35429df"
client_secret = "7136832d-01be-456a-a1fe-25c7f9e130c5"

pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
async def test_fetch_demo_igent():
    consumer = Obelisk(client=client_id, secret=client_secret)
    result = await consumer.fetch_single_chunk(
        datasets=["612f6c39cbceda0ea9753d95"],
        metrics=["org.dyamand.types.common.Temperature::number"],
        from_timestamp=1740924034000,
        to_timestamp=1741100614258,
        limit=2
    )

    assert len(result.items) == 2
