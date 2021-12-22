"""Obelisk Server-Sent Events example."""

__author__ = 'Pieter Moens'
__email__ = 'Pieter.Moens@UGent.be'

import json
import logging

from rx import Observable, Observer

from example.config import ObeliskConfig
from obelisk.consumer import ObeliskConsumer


class ObeliskObserver(Observer):
    """Observer class to consume Server-Sent Events."""
    def __init__(self):
        self.logger = ObeliskConfig.logger
        self.logger.name = __name__

    def on_next(self, message):
        """Consume event."""
        try:
            _json = json.loads(message.data)
            self.logger.info('Received %s', _json)
        except TypeError:
            self.logger.warning('Error parsing message in ObeliskObserver: %s', message.data)
        except json.JSONDecodeError:
            self.logger.warning('Error parsing message in ObeliskObserver: %s', message.data)

    def on_completed(self):
        """Completed event."""
        self.logger.info('ObeliskObserver completed!')

    def on_error(self, error):
        """Handle error event."""
        self.logger.error('Error occurred in ObeliskObserver: %s', error)


if __name__ == '__main__':
    logging.getLogger('obelisk').propagate = True
    name = 'test.obelisk-python'
    datasets = ['60a6665536e9be3139e58f7b']
    metrics = ['event::json']

    c = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET, debug=True)
    observer = ObeliskObserver()

    ObeliskConfig.logger.info('Starting SSE consumer ...')

    stream_id, stream = c.sse(name, datasets, metrics)
    Observable.from_(stream.events())\
        .filter(lambda msg: msg.data)\
        .subscribe(observer)
