from __future__ import annotations

from typing import Protocol, runtime_checkable

from afrinograph.modules.source_contract.application.contracts import (
    CollectionRequest,
    CollectionResult,
)
from afrinograph.modules.source_contract.domain.capabilities import SourceCapability


@runtime_checkable
class SourceAdapter(Protocol):
    def capabilities(self) -> frozenset[SourceCapability]: ...

    async def collect(self, request: CollectionRequest) -> CollectionResult: ...
