"""
Various retry strategies, from no retry to exponential backoff.
"""

from asyncio import sleep
from abc import ABC, abstractmethod
from datetime import timedelta

class RetryEvaluator(ABC):
    """
    This class performs the actual retry handling.
    It can keep track of internal state as it so wishes,
    to perform the function of :meth:`should_retry`.
    """

    @abstractmethod
    async def should_retry(self) -> bool:
        """
        This method should return True if the strategy should retry,
        but may wait internally if it deems necessary.
        """
        pass

class RetryStrategy(ABC):
    """
    Base class for all retry strategies, whether predefined or user-made.
    The strategy has as its sole purpose to create instances of :class:`RetryEvaluator`
    that can be used for a specific operation.

    Each individual failable operation will request a separate evaluator using the make method.
    """

    @abstractmethod
    def make(self) -> RetryEvaluator:
        """
        Create an instance of a RetryEvaluator.
        Custom strategies should also subclass RetryEvaluator
        """
        pass

class NoRetryStrategy(RetryStrategy):
    """
    Retry strategy that simply does not retry.
    """
    def make(self) -> RetryEvaluator:
        class NoRetryEvaluator(RetryEvaluator):
            async def should_retry(self) -> bool:
                return False

        return NoRetryEvaluator()

class ImmediateRetryStrategy(RetryStrategy):
    """
    Retry strategy that tries again without delay,
    up to a user defined maximum amount of times.
    """
    def __init__(self, max_retries: int) -> None:
        self.max_retries = max_retries

    def make(self) -> RetryEvaluator:
        class ImmediateRetryEvaluator(RetryEvaluator):
            count: int = 0
            max_retries: int = self.max_retries
            async def should_retry(self) -> bool:
                if self.count >= self.max_retries:
                    return False
                self.count += 1
                return True

        return ImmediateRetryEvaluator()

class ExponentialBackoffStrategy(RetryStrategy):
    """
    Retry strategy implementing the exponential backoff algorithm.
    Every failure up to `max_retries` will result in a sleep
    of t ** n seconds, with t being the backoff and n amount of failures.

    Note that backoff values less than one second will count as zero.
    """
    max_retries: int
    backoff: timedelta
    max_backoff: timedelta

    def __init__(self, max_retries: int = 5,
                 backoff: timedelta = timedelta(seconds=2),
                 max_backoff: timedelta = timedelta(hours=24)) -> None:
        self.max_retries = max_retries
        self.backoff = backoff
        self.max_backoff = max_backoff

    def make(self) -> RetryEvaluator:
        class ExponentialBackoffEvaluator(RetryEvaluator):
            count: int = 0
            max_retries: int = self.max_retries
            backoff: timedelta = self.backoff
            max_backoff: timedelta = self.max_backoff

            async def should_retry(self) -> bool:
                if self.count >= self.max_retries:
                    return False
                self.count += 1
                await sleep(
                    min(self.max_backoff.seconds, self.backoff.seconds ** self.count))
                return True

        return ExponentialBackoffEvaluator()
