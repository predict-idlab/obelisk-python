"""
This module provides wrappers for the classes in :mod:`obelisk.asynchronous` with a synchronous API.
These hold on to a private event loop and block until a result is available.

Note
----

Please note that the sync module *will not* work in an asynchronous context (i.e. in any method returning a Future, or a Jupyter notebook).
This is because it is internally nothing more than a wrapper over the asynchronous implementation.
Use the asynchronous implementation in these situations.
"""
__all__ = ["Obelisk"]
from .client import Obelisk
