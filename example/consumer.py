"""Obelisk consumer example."""

__author__ = 'Pieter Moens'
__email__ = 'Pieter.Moens@UGent.be'

from example.config import ObeliskConfig
from obelisk import ObeliskConsumer

if __name__ == '__main__':
    c = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)
    r = c.get_datasets(limit=2)
    print(r)
    r = c.get_dataset('60a6665536e9be3139e58f7b')
    print(r)
    r = c.get_metrics('60a6665536e9be3139e58f7b')
    print(r)
    r = c.get_metric('60a6665536e9be3139e58f7b', 'event::json')
    print(r)
    r = c.get_things('60a6665536e9be3139e58f7b')
    print(r)
    r = c.get_thing('60a6665536e9be3139e58f7b', 'BBB7')
    print(r)

    r = c.events(['60a6665536e9be3139e58f7b'], metrics=['event::json'])
    print(r)
