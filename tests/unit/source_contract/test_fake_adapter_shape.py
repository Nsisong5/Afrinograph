from __future__ import annotations

import pytest

from afrinograph.modules.source_contract.application.contracts import (
    CollectionMode,
    CollectionRequest,
)
from afrinograph.modules.source_contract.application.ports import SourceAdapter
from afrinograph.modules.source_contract.domain.capabilities import SourceCapability
from afrinograph.modules.source_contract.domain.errors import InvalidCheckpointError
from afrinograph.modules.source_contract.domain.items import RawSourceItem
from afrinograph.shared.infrastructure.clock import SystemClock
from tests.fakes.fake_source_adapter import FakeSourceAdapter


@pytest.mark.unit
def test_fake_adapter_satisfies_protocol() -> None:
    clock = SystemClock()
    adapter = FakeSourceAdapter(
        batches=[],
        capabilities=frozenset({SourceCapability.CURSOR_PAGINATION}),
        clock=clock,
    )
    assert isinstance(adapter, SourceAdapter)


@pytest.mark.unit
async def test_fake_adapter_pagination_sequence() -> None:
    clock = SystemClock()
    item1 = RawSourceItem(source_item_type="post", raw_payload="1")
    item2 = RawSourceItem(source_item_type="post", raw_payload="2")
    item3 = RawSourceItem(source_item_type="post", raw_payload="3")

    adapter = FakeSourceAdapter(
        batches=[[item1], [item2], [item3]],
        capabilities=frozenset({SourceCapability.CURSOR_PAGINATION}),
        clock=clock,
    )

    req1 = CollectionRequest(source_id="src_1", mode=CollectionMode.FULL)
    res1 = await adapter.collect(req1)
    assert res1.items == [item1]
    assert res1.has_more is True
    assert res1.next_checkpoint == "batch_1"

    req2 = CollectionRequest(source_id="src_1", mode=CollectionMode.FULL, checkpoint=res1.next_checkpoint)
    res2 = await adapter.collect(req2)
    assert res2.items == [item2]
    assert res2.has_more is True
    assert res2.next_checkpoint == "batch_2"

    req3 = CollectionRequest(source_id="src_1", mode=CollectionMode.FULL, checkpoint=res2.next_checkpoint)
    res3 = await adapter.collect(req3)
    assert res3.items == [item3]
    assert res3.has_more is False
    assert res3.next_checkpoint is None

    # 4th call past end
    req4 = CollectionRequest(source_id="src_1", mode=CollectionMode.FULL, checkpoint="batch_3")
    res4 = await adapter.collect(req4)
    assert res4.items == []
    assert res4.has_more is False
    assert res4.next_checkpoint is None


@pytest.mark.unit
async def test_fake_adapter_invalid_checkpoint() -> None:
    clock = SystemClock()
    adapter = FakeSourceAdapter(
        batches=[],
        capabilities=frozenset(),
        clock=clock,
    )
    req = CollectionRequest(source_id="src_1", mode=CollectionMode.FULL, checkpoint="invalid")
    with pytest.raises(InvalidCheckpointError):
        await adapter.collect(req)
