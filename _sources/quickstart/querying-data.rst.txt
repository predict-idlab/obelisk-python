Querying Data
=============

Documentation
-------------

Read the official `documentation <https://obelisk.docs.apiary.io/#/reference/data-api/querying-data>`_.


Getting Raw Events
------------------

Basic example::

    from obelisk import ObeliskConsumer
    from example.config import ObeliskConfig

    consumer = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)
    response = consumer.events('60a6665536e9be3139e58f7b', metrics=['event::json'])

Manipulating and Filtering Events
---------------------------------

Using TimestampPrecision [SECONDS, MILLISECONDS, MICROSECONDS]::

    from obelisk import ObeliskConsumer
    from obelisk.schema import TimestampPrecision
    from example.config import ObeliskConfig

    consumer = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)
    response = consumer.events('60a6665536e9be3139e58f7b', metrics=['event::json'], precision=TimestampPrecision.SECONDS)

Using `EventField <https://obelisk.docs.apiary.io/#/data-structures/0/stats-field>`_::

    from obelisk import ObeliskConsumer
    from obelisk.schema import EventField
    from example.config import ObeliskConfig

    consumer = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)

    fields = [EventField.TIMESTAMP, EventField.VALUE]
    response = consumer.events('60a6665536e9be3139e58f7b', metrics=['event::json'], fields=fields)

Using `FilterExpression <https://obelisk.docs.apiary.io/#/data-structures/0/filter-expression>`_::

    from obelisk import ObeliskConsumer
    from example.config import ObeliskConfig

    consumer = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)

    filter_thing = {  # Filter based on a Thing ID
        'source': {
            '_eq': 'event.breakpoint.algo2'
        }
    }
    response = consumer.events(['60a6665536e9be3139e58f7b'], metrics=['event::json'], filter_=filter_thing)
