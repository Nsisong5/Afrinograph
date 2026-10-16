from __future__ import annotations

import pytest

from afrinograph.modules.source_contract.domain.capabilities import SourceCapability
from afrinograph.modules.source_contract.domain.items import RawSourceItem
from afrinograph.shared.infrastructure.clock import SystemClock
from tests.contract.source_adapter_contract import assert_adapter_conforms
from tests.fakes.fake_source_adapter import FakeSourceAdapter


@pytest.mark.contract
async def test_fake_adapter_conforms_to_contract() -> None:
    clock = SystemClock()
    item = RawSourceItem(source_item_type="post", raw_payload="contract test payload")
    adapter = FakeSourceAdapter(
        batches=[[item]],
        capabilities=frozenset({SourceCapability.CURSOR_PAGINATION}),
        clock=clock,
    )
    await assert_adapter_conforms(adapter)
