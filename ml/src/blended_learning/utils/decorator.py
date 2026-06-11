from typing import Callable
from functools import wraps
import time


def execution_time(func: Callable) -> Callable:
    """
    Decorator to measure and print function execution time (2 decimal precision).
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()

        result = func(*args, **kwargs)

        end_time = time.perf_counter()
        duration = end_time - start_time

        minutes = duration / 60
        seconds = duration % 60

        print(
            f"{func.__name__} executed in "
            f"{minutes:.2f} min ({seconds:.2f} sec)"
        )

        return result

    return wrapper