Getting Started with Obelisk
============================

Installation
------------

Obelisk Consumer
----------------

ObeliskConsumer example::

    from obelisk.consumer import ObeliskConsumer
    from example.config import ObeliskConfig

    consumer = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)
    response = consumer.events('60a6665536e9be3139e58f7b', metrics=['temperature.celsius::number'])

Obelisk Producer
----------------

ObeliskProducer example::

    from example.config import ObeliskConfig
    from obelisk.models import TimestampPrecision, IngestMode
    from obelisk.producer import ObeliskProducer

    c = ObeliskProducer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)
    data = [
        {
            'metric': 'event::json',
            'value': {'test': 'check'}
        }
    ]
    response = c.send(dataset='60a6665536e9be3139e58f7b', data=data, precision=TimestampPrecision.MILLISECONDS,
                      mode=IngestMode.DEFAULT)
