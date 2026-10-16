from __future__ import annotations

import pytest

from afrinograph.modules.source_contract.domain.capabilities import SourceCapability


@pytest.mark.unit
def test_capabilities_count_and_distinct() -> None:
    expected_capabilities = {
        "INCREMENTAL_COLLECTION",
        "HISTORICAL_BACKFILL",
        "CURSOR_PAGINATION",
        "TIME_WINDOW_COLLECTION",
        "STABLE_ITEM_IDENTIFIERS",
        "UPDATE_DETECTION",
        "DELETION_DETECTION",
        "RATE_LIMIT_METADATA",
    }
    actual_names = {cap.name for cap in SourceCapability}
    assert actual_names == expected_capabilities
    assert len(SourceCapability) == len(expected_capabilities)
