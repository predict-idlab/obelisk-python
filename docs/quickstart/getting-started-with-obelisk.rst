Getting Started with Obelisk
============================

Installation
------------

Assuming you have Python already, install Obelisk::

    pip install --upgrade obelisk-python --no-deps --index-url https://gitlab+deploy-token-pip:fq5hPPobixza9-mVzuN9@gitlab.ilabt.imec.be/api/v4/projects/2082/packages/pypi/simple


Adding the package to ``requirements.txt``::

    https://gitlab+deploy-token-pip:fq5hPPobixza9-mVzuN9@gitlab.ilabt.imec.be/api/v4/projects/2082/packages/pypi/simple#egg=obelisk-python


Obelisk Consumer
----------------

ObeliskConsumer example::

    from obelisk.consumer import ObeliskConsumer
    from example.config import ObeliskConfig

    consumer = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET, api_version='v2')
    response = consumer.events('playground.city', 'temperature.celsius::number')

Obelisk Producer
----------------

ObeliskProducer example::

    from obelisk.consumer import ObeliskProducer
    from example.config import ObeliskConfig

    producer = ObeliskProducer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET, api_version='v2')
    data = [
        [1574675693000, 'temperature.celsius::number', 'test', 24.5]
    ]
    status, response = producer.send(scope='playground.city', data=data)
