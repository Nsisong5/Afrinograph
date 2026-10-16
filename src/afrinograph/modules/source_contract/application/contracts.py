from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

from afrinograph.modules.source_contract.domain.items import RawSourceItem


class CollectionMode(Enum):
    FULL = auto()
    INCREMENTAL = auto()
    BACKFILL = auto()


@dataclass(frozen=True)
class CollectionRequest:
    source_id: str
    mode: CollectionMode
    window_start: datetime | None = None
    window_end: datetime | None = None
    checkpoint: str | None = None
    max_items: int | None = None

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id must be non-empty")
        if self.max_items is not None and self.max_items <= 0:
            raise ValueError("max_items must be greater than 0 if provided")
        if self.window_start is not None and self.window_start.tzinfo is None:
            raise ValueError("window_start must be timezone-aware")
        if self.window_end is not None and self.window_end.tzinfo is None:
            raise ValueError("window_end must be timezone-aware")


@dataclass(frozen=True)
class CollectionResult:
    items: list[RawSourceItem] = field(default_factory=list)
    next_checkpoint: str | None = None
    has_more: bool = False
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.has_more and self.next_checkpoint is None:
            raise ValueError("has_more=True requires a non-None next_checkpoint")
