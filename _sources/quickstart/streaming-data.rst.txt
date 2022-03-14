Streaming Data (Server-Sent Events)
===================================

Documentation
-------------

Read the official `documentation <https://obelisk.docs.apiary.io/#/reference/data-api/streaming-data>`_.

Opening a Stream
----------------

Example::

    name = 'test.obelisk-python'  # Name of the stream (must be unique)
    datasets = ['60a6665536e9be3139e58f7b']  # Dataset(s) to consume from
    metrics = ['event::json']  # Metric(s) to consume

    consumer = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET, debug=True)

    stream_id, stream = consumer.sse(name, datasets, metrics)


Consuming Streaming Data
------------------------

Example::

    class ObeliskObserver(Observer):
        """Observer class to consume Server-Sent Events."""
        def __init__(self):
            self.logger = logging.getLogger(__name__)

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


    observer = ObeliskObserver()

    # Retrieving the streaming data
    Observable.from_(stream.events())\
        .filter(lambda msg: msg.data)\
        .subscribe(observer)

In this example, all received events are simply logged. Edit the `on_next` method to process the events per your use-case.
