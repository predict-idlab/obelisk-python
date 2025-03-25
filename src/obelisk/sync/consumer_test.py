from .consumer import Consumer

def test_demo_igent():
    consumer = Consumer(client="67c716e616c11421cfe2faf6", secret="08dafe89-0389-45b4-9832-cc565fb8c2eb")
    result = consumer.single_chunk(
        datasets=["612f6c39cbceda0ea9753d95"],
        metrics=["org.dyamand.types.common.Temperature::number"],
        from_timestamp=1740924034000,
        to_timestamp=1741100614258,
        limit=2
    )

    assert len(result.items) == 2

def test_two_instances():
    consumer_one = Consumer(client="67c716e616c11421cfe2faf6", secret="08dafe89-0389-45b4-9832-cc565fb8c2eb")
    consumer_two = Consumer(client="67c716e616c11421cfe2faf6", secret="08dafe89-0389-45b4-9832-cc565fb8c2eb")
    result_one = consumer_one.single_chunk(
        datasets=["612f6c39cbceda0ea9753d95"],
        metrics=["org.dyamand.types.common.Temperature::number"],
        from_timestamp=1740924034000,
        to_timestamp=1741100614258,
        limit=2
    )
    result_two = consumer_one.single_chunk(
        datasets=["612f6c39cbceda0ea9753d95"],
        metrics=["org.dyamand.types.common.Temperature::number"],
        from_timestamp=1740924034000,
        to_timestamp=1741100614258,
        limit=2
    )
    assert len(result_one.items) == 2
    assert len(result_two.items) == 2
