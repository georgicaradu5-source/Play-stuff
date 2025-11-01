import logging
import os
import random
import time
from functools import wraps
from typing import Any, Callable, Iterable, Tuple


def setup_logger(name: str = "agent_x", level: int = logging.INFO) -> logging.Logger:
    """Configure root logger with console and optional file handlers.

    Logs to stdout and, if data/ exists, also to data/agent.log.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    log_path = os.path.join(log_dir, "agent.log")
    try:
        os.makedirs(log_dir, exist_ok=True)
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        # Non-fatal if file logging can't be set up
        pass

    return logger


def sleep_with_jitter(bounds: Tuple[int, int]) -> None:
    low, high = bounds
    delay = random.uniform(low, high)
    time.sleep(delay)


def backoff_retry(
    exceptions: Tuple[type, ...],
    tries: int = 5,
    base_delay: float = 1.0,
    jitter: Tuple[float, float] = (0.2, 0.8),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Exponential backoff with jitter.

    Args:
        exceptions: Exception types to retry on.
        tries: Max attempts.
        base_delay: Initial delay seconds.
        jitter: Uniform random jitter added each attempt.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = base_delay
            last_err: Exception | None = None
            for attempt in range(1, tries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:  # type: ignore[misc]
                    last_err = e
                    if attempt == tries:
                        raise
                    jitter_val = random.uniform(*jitter)
                    time.sleep(delay + jitter_val)
                    delay *= 2
            assert last_err is not None
            raise last_err

        return wrapper

    return decorator


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def chunk(iterable: Iterable[Any], size: int) -> Iterable[list[Any]]:
    buf: list[Any] = []
    for item in iterable:
        buf.append(item)
        if len(buf) == size:
            yield buf
            buf = []
    if buf:
        yield buf

