"""Obelisk consumer example."""

__author__ = 'Pieter Moens'
__email__ = 'Pieter.Moens@UGent.be'

from example.config import ObeliskConfig
from obelisk import ObeliskConsumer

if __name__ == '__main__':
    consumer = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)

    # Getting datasets
    datasets = consumer.get_datasets(limit=2)

    # Get information about a single dataset
    dataset = consumer.get_dataset(dataset='60a6665536e9be3139e58f7b')

    # Get available metrics for a dataset
    metrics = consumer.get_metrics(dataset='60a6665536e9be3139e58f7b')

    # Get information about a single metric
    metric = consumer.get_metric(dataset='60a6665536e9be3139e58f7b', metric='event::json')

    # Get available things for a dataset
    things = consumer.get_things(dataset='60a6665536e9be3139e58f7b')

    # Get information about a single thing
    thing = consumer.get_thing(dataset='60a6665536e9be3139e58f7b', thing='BBB7')

    # https://obelisk.docs.apiary.io/#/data-structures/0/filter-expression
    filter_thing = {
        'source': {
            '_eq': 'event.breakpoint.algo2'
        }
    }
    events = consumer.events(['60a6665536e9be3139e58f7b'], metrics=['event::json'], filter_=filter_thing)
