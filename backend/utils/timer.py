"""timer.py - measure processing time."""

import time


class Timer:
    """Context manager: `with Timer() as t: ...` then read t.seconds."""

    def __enter__(self):
        self.start = time.perf_counter()
        self.seconds = 0.0
        return self

    def __exit__(self, *exc):
        self.seconds = time.perf_counter() - self.start
        return False
