Ingesting Data
==============

Documentation
-------------

Read the official `documentation <https://obelisk.docs.apiary.io/#/reference/data-api/ingesting-data>`_.


Uploading Events
----------------

Basic example::

    from obelisk import ObeliskProducer
    from example.config import ObeliskConfig

    producer = ObeliskProducer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)

    data = [
        {
            'metric': 'event::json',
            'value': {'test': 'check'}
        }
    ]
    response = c.send(dataset='60a6665536e9be3139e58f7b', data=data)

IngestMode::

    from obelisk import ObeliskProducer
    from obelisk.producer import IngestMode
    from example.config import ObeliskConfig

    producer = ObeliskProducer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)

    data = [
        {
            'metric': 'event::json',
            'value': {'test': 'check'}
        }
    ]
    response = c.send(dataset='60a6665536e9be3139e58f7b', data=data, mode=IngestMode.STORE_ONLY)  # Ingested data will not be streamed

Specify TimestampPrecision::

    from obelisk import ObeliskProducer
    from obelisk.schema import TimestampPrecision
    from example.config import ObeliskConfig

    producer = ObeliskProducer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)

    data = [
        {
            'metric': 'event::json',
            'value': {'test': 'check'}
        }
    ]
    response = producer.send(dataset='60a6665536e9be3139e58f7b', data=data, precision=TimestampPrecision.SECONDS)
