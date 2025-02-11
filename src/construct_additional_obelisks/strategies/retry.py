from asyncio import sleep
from abc import ABC, abstractmethod
from datetime import timedelta

class RetryEvaluator(ABC):
    @abstractmethod
    async def should_retry(self) -> bool:
        """
        This method should return True if the strategy should retry,
        but may wait internally if it deems necessary.
        :return:
        """
        pass

class RetryStrategy(ABC):
    @abstractmethod
    def make(self) -> RetryEvaluator:
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

    def __init__(self, max_retries: int = 5,
                 backoff: timedelta = timedelta(seconds=2)) -> None:
        self.max_retries = max_retries
        self.backoff = backoff

    def make(self) -> RetryEvaluator:
        class ExponentialBackoffEvaluator(RetryEvaluator):
            count: int = 0
            max_retries: int = self.max_retries
            backoff: timedelta = self.backoff

            async def should_retry(self) -> bool:
                if self.count >= self.max_retries:
                    return False
                self.count += 1
                await sleep(self.backoff.seconds)
                return True

        return ExponentialBackoffEvaluator()