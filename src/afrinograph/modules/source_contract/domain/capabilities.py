from __future__ import annotations

from enum import Enum, auto


class SourceCapability(Enum):
    INCREMENTAL_COLLECTION = auto()
    HISTORICAL_BACKFILL = auto()
    CURSOR_PAGINATION = auto()
    TIME_WINDOW_COLLECTION = auto()
    STABLE_ITEM_IDENTIFIERS = auto()
    UPDATE_DETECTION = auto()
    DELETION_DETECTION = auto()
    RATE_LIMIT_METADATA = auto()
