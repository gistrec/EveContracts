import time
import logging
from typing import Optional

class ExecutionTimer:
    """
    Simple timing context manager that logs elapsed time to console.
    Usage: with ExecutionTimer(\"fetch page\"): ...
    """
    def __init__(self, label: str, extra: Optional[str] = None):
        self.label = label
        self.extra = extra
        self._start = 0.0

    def __enter__(self):
        self._start = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.monotonic() - self._start
        msg = f"{self.label} took {elapsed:.2f}s"
        if self.extra:
            msg += f" ({self.extra})"
        logging.info(msg)
        # do not suppress exceptions
        return False
