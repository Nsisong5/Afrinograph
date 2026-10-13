from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Protocol for getting current time, enabling deterministic testing."""

    def now(self) -> datetime:
        ...
