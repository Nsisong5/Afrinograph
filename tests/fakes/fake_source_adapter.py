from __future__ import annotations

from typing import Sequence

from afrinograph.modules.source_contract.application.contracts import (
    CollectionRequest,
    CollectionResult,
)
from afrinograph.modules.source_contract.domain.capabilities import SourceCapability
from afrinograph.modules.source_contract.domain.errors import (
    AdapterError,
    InvalidCheckpointError,
)
from afrinograph.modules.source_contract.domain.items import RawSourceItem
from afrinograph.shared.application.ports import Clock


class FakeSourceAdapter:
    def __init__(
        self,
        batches: Sequence[Sequence[RawSourceItem]],
        capabilities: frozenset[SourceCapability],
        clock: Clock,
        should_fail_with: Exception | None = None,
    ) -> None:
        self._batches = list(batches)
        self._capabilities = capabilities
        self._clock = clock
        self._should_fail_with = should_fail_with
        self._next_batch_index = 0

    def capabilities(self) -> frozenset[SourceCapability]:
        return self._capabilities

    async def collect(self, request: CollectionRequest) -> CollectionResult:
        if self._should_fail_with is not None:
            err = self._should_fail_with
            if not isinstance(err, AdapterError):
                raise AdapterError(str(err), retryable=False) from err
            raise err

        if request.checkpoint is not None:
            if request.checkpoint.startswith("batch_"):
                try:
                    idx = int(request.checkpoint.split("_")[1])
                    self._next_batch_index = idx
                except (ValueError, IndexError) as e:
                    raise InvalidCheckpointError(f"Invalid checkpoint: {request.checkpoint}") from e
            elif request.checkpoint == "invalid":
                raise InvalidCheckpointError("Invalid checkpoint token")

        if self._next_batch_index >= len(self._batches):
            return CollectionResult(items=[], next_checkpoint=None, has_more=False)

        batch = list(self._batches[self._next_batch_index])

        if request.max_items is not None and len(batch) > request.max_items:
            batch = batch[: request.max_items]

        self._next_batch_index += 1
        has_more = self._next_batch_index < len(self._batches)
        next_checkpoint = f"batch_{self._next_batch_index}" if has_more else None

        return CollectionResult(
            items=batch,
            next_checkpoint=next_checkpoint,
            has_more=has_more,
        )
