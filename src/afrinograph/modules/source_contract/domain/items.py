from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
import json
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class RawSourceItem:
    source_item_id: str | None = None
    source_item_type: str = ""
    title: str | None = None
    content_text: str | None = None
    original_url: str | None = None
    raw_payload: str | bytes = b""
    provider_metadata: Mapping[str, Any] = field(default_factory=dict)
    source_published_at: datetime | None = None
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.source_item_type:
            raise ValueError("source_item_type must be non-empty")
        if self.source_item_id is not None and not self.source_item_id:
            raise ValueError("source_item_id, if provided, must be non-empty (use None for no ID)")
        if not self.raw_payload:
            raise ValueError("raw_payload must be non-empty")
        if self.source_published_at is not None and self.source_published_at.tzinfo is None:
            raise ValueError("source_published_at must be timezone-aware")
        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware")

        try:
            json.dumps(self.provider_metadata)
        except (TypeError, ValueError) as e:
            raise ValueError(f"provider_metadata must be JSON serializable: {e}") from e

        if not isinstance(self.provider_metadata, MappingProxyType):
            object.__setattr__(self, "provider_metadata", MappingProxyType(dict(self.provider_metadata)))
