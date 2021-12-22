Getting Started with Obelisk
============================

Installation
------------

PyPI installation::

    pip install obelisk-py




Obelisk Consumer
----------------

ObeliskConsumer example::

    from obelisk import ObeliskConsumer
    from example.config import ObeliskConfig

    consumer = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)
    response = consumer.events('60a6665536e9be3139e58f7b', metrics=['temperature.celsius::number'])

Obelisk Producer
----------------

ObeliskProducer example::

    from obelisk import ObeliskProducer
    from obelisk.producer import IngestMode
    from obelisk.schema import TimestampPrecision
    from example.config import ObeliskConfig

    producer = ObeliskProducer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET, debug=True)
    data = [
        {
            'metric': 'event::json',
            'value': {'test': 'check'}
        }
    ]
    response = producer.send(dataset='60a6665536e9be3139e58f7b', data=data, precision=TimestampPrecision.MILLISECONDS,
                      mode=IngestMode.DEFAULT)

Obelisk API Documentation
----------------
More information about the Obelisk API can be found in the official `documentation <https://obelisk.docs.apiary.io/>`_.
