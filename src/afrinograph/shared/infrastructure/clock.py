from datetime import datetime

from afrinograph.shared.domain.value_objects import utc_now


class SystemClock:
    """System implementation of Clock using actual system time."""

    def now(self) -> datetime:
        return utc_now()
