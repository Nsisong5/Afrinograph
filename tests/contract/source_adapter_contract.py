from __future__ import annotations

from afrinograph.modules.source_contract.application.contracts import (
    CollectionMode,
    CollectionRequest,
    CollectionResult,
)
from afrinograph.modules.source_contract.application.ports import SourceAdapter
from afrinograph.modules.source_contract.domain.capabilities import SourceCapability


async def assert_adapter_conforms(adapter: SourceAdapter) -> None:
    """Asserts that a given SourceAdapter conforms to the contract rules."""
    caps = adapter.capabilities()
    assert isinstance(caps, frozenset)
    for cap in caps:
        assert isinstance(cap, SourceCapability)

    req = CollectionRequest(source_id="contract_test_src", mode=CollectionMode.FULL)
    res = await adapter.collect(req)
    assert isinstance(res, CollectionResult)
    assert isinstance(res.items, list)
    assert isinstance(res.has_more, bool)
    assert isinstance(res.warnings, list)
    if not res.has_more:
        assert res.next_checkpoint is None

    for item in res.items:
        assert item.source_item_type
        assert item.raw_payload is not None
        assert item.source_item_id is None or isinstance(item.source_item_id, str)
        assert item.source_published_at is None or hasattr(item.source_published_at, "tzinfo")
