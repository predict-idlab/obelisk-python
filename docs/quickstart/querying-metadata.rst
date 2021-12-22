Querying MetaData
=================

Documentation
-------------

Read the official `documentation <https://obelisk.docs.apiary.io/#/reference/catalog-api>`_.


Retrieving Metadata
-------------------

Basic example::

    from obelisk import ObeliskClient
    from example.config import ObeliskConfig

    client = ObeliskClient(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)

    # Getting datasets
    response = client.get_datasets(limit=2)

    # Get information about a single dataset
    response = client.get_dataset(dataset='60a6665536e9be3139e58f7b')

    # Get available metrics for a dataset
    response = client.get_metrics(dataset='60a6665536e9be3139e58f7b')

    # Get information about a single metric
    response = client.get_metric(dataset='60a6665536e9be3139e58f7b', metric='event::json')

    # Get available things for a dataset
    response = client.get_things(dataset='60a6665536e9be3139e58f7b')

    # Get information about a single thing
    response = client.get_thing(dataset='60a6665536e9be3139e58f7b', thing='BBB7')
