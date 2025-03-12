"""
Obelisk-py is a client for the Obelisk data platform.
We support both "classic" Obelisk and HFS,
each with a synchronous and async API.
The PyPi package name is ``obelisk-py``, the Python module is called ``obelisk``.

Your starting point will be one of the Consumer or Producer instances in :mod:`~.sync` or :mod:`~.asynchronous` depending on your preferred API.

Each of the `sync` or `asynchronous` modules will contain two main classes, those being Producer and Consumer.
Those submit or fetch data respectively.

Error handling
--------------

Obelisk-py comes with robust retry logic to handle any errors that may come up.
Issues like timeouts, temporary server errors or even DNS issues are fairly common, and handling them properly is important.
Each Client accepts a retry strategy of type :class:`~.strategies.retry.RetryStrategy`.
Several predefined strategies are available in :mod:`.strategies.retry`.
"""
