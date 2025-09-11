"""
This module contains the asynchronous API to Obelisk-py.
These methods all return an :external+python:class:`collections.abc.Awaitable`.

Relevant entrance points are :class:`client.Obelisk`.
It can be imported from the :mod:`.client` module, or directly from this one.
"""
__all__= ['Obelisk', 'core']
from .client import Obelisk
from . import core
