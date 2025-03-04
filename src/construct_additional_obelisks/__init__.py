"""
Construct Additional Obelisks is a client for the Obelisk data platform.
We support both "classic" Obelisk and HFS,
each with a synchronous and async API.

Your starting point will be one of the Consumer or Producer instances in `sync` or `asynchronous` depending on your preferred API.

Each of th `sync` or `asynchronous` modules will contain two main classes, those being Producer and Consumer.
Those submit or fetch data respectively.

## Error handling

Construct Additional Obelisks comes with robust retry logic to handle any errors that may come up.
Issues like timeouts, temporary server errors or even DNS issues are fairly common, and handling them properly is important.
Each Client accepts a retry strategy of type `strategies.retry.RetryStrategy`.
Several predefined strategies are available in `strategies.retry`.
"""
