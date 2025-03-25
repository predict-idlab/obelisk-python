"""
This module provides wrappers for the classes in `obelisk.asynchronous` with a synchronous API.
These hold on to a private event loop and block until a result is available.

There is no synchronous alternative to `obelisk.asynchronous.client.Client`.

Note
----

Please note that the sync module *will not* work in an asynchronous context (i.e. in any method returning a Future, or a Jupyter notebook).
This is because it is internally nothing more than a wrapper over the asynchronous implementation.
Use the asynchronous implementation in these situations.
"""
