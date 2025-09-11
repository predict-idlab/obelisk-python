from obelisk.sync import Obelisk

client_id = "682c6c46604b3b3be35429df"
client_secret = "7136832d-01be-456a-a1fe-25c7f9e130c5"

def test_demo_igent_fetch():
    consumer = Obelisk(client=client_id, secret=client_secret)
    result = consumer.fetch_single_chunk(
        datasets=["612f6c39cbceda0ea9753d95"],
        metrics=["org.dyamand.types.common.Temperature::number"],
        from_timestamp=1740924034000,
        to_timestamp=1741100614258,
        limit=2
    )

    assert len(result.items) == 2

def test_two_instances():
    consumer_one = Obelisk(client=client_id, secret=client_secret)
    consumer_two = Obelisk(client=client_id, secret=client_secret)
    result_one = consumer_one.fetch_single_chunk(
        datasets=["612f6c39cbceda0ea9753d95"],
        metrics=["org.dyamand.types.common.Temperature::number"],
        from_timestamp=1740924034000,
        to_timestamp=1741100614258,
        limit=2
    )
    result_two = consumer_two.fetch_single_chunk(
        datasets=["612f6c39cbceda0ea9753d95"],
        metrics=["org.dyamand.types.common.Temperature::number"],
        from_timestamp=1740924034000,
        to_timestamp=1741100614258,
        limit=2
    )
    assert len(result_one.items) == 2
    assert len(result_two.items) == 2
