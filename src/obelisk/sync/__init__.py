"""
This module provides wrappers for the classes in `obelisk.asynchronous` with a synchronous API.
These hold on to a private event loop and block until a result is available.

There is no synchronous alternative to `obelisk.asynchronous.client.Client`.
"""
