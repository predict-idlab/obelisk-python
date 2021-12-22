"""Obelisk producer example."""

__author__ = 'Pieter Moens'
__email__ = 'Pieter.Moens@UGent.be'

from example.config import ObeliskConfig
from obelisk.producer import ObeliskProducer
from obelisk.models import TimestampPrecision, IngestMode

logger = ObeliskConfig.logger
logger.name = __name__

if __name__ == '__main__':
    c = ObeliskProducer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET, debug=True)
    data = [
        {
            'metric': 'event::json',
            'value': {'test': 'check'}
        }
    ]
    response = c.send(dataset='60a6665536e9be3139e58f7b', data=data, precision=TimestampPrecision.MILLISECONDS,
                      mode=IngestMode.DEFAULT)
    logger.info('Data sent')
