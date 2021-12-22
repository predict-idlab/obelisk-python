"""Obelisk producer example."""

__author__ = 'Pieter Moens'
__email__ = 'Pieter.Moens@UGent.be'

from example.config import ObeliskConfig
from obelisk import ObeliskProducer
from obelisk.producer import IngestMode
from obelisk.schema import TimestampPrecision

if __name__ == '__main__':
    producer = ObeliskProducer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET, debug=True)
    data = [
        {
            'metric': 'event::json',
            'value': {'test': 'check'}
        }
    ]
    response = producer.send(dataset='60a6665536e9be3139e58f7b', data=data, precision=TimestampPrecision.MILLISECONDS,
                             mode=IngestMode.DEFAULT)
