import pytest
from .consumer import Consumer

pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
async def test_demo_igent():
    consumer = Consumer(client="67c716e616c11421cfe2faf6", secret="08dafe89-0389-45b4-9832-cc565fb8c2eb")
    result = await consumer.single_chunk(
        datasets=["612f6c39cbceda0ea9753d95"],
        metrics=["org.dyamand.types.common.Temperature::number"],
        from_timestamp=1740924034000,
        to_timestamp=1741100614258,
        limit=2
    )

    assert len(result.items) == 2
