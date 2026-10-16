from __future__ import annotations

from datetime import UTC, datetime
import pytest

from afrinograph.modules.source_contract.application.contracts import (
    CollectionMode,
    CollectionRequest,
    CollectionResult,
)
from afrinograph.modules.source_contract.domain.items import RawSourceItem


@pytest.mark.unit
def test_collection_request_valid() -> None:
    req = CollectionRequest(
        source_id="src_1",
        mode=CollectionMode.INCREMENTAL,
        window_start=datetime.now(UTC),
        window_end=datetime.now(UTC),
        checkpoint="ckpt_1",
        max_items=10,
    )
    assert req.source_id == "src_1"
    assert req.mode == CollectionMode.INCREMENTAL
    assert req.max_items == 10


@pytest.mark.unit
def test_collection_request_invalid_source_id() -> None:
    with pytest.raises(ValueError):
        CollectionRequest(source_id="", mode=CollectionMode.FULL)


@pytest.mark.unit
def test_collection_request_invalid_max_items() -> None:
    with pytest.raises(ValueError):
        CollectionRequest(source_id="src_1", mode=CollectionMode.FULL, max_items=0)
    with pytest.raises(ValueError):
        CollectionRequest(source_id="src_1", mode=CollectionMode.FULL, max_items=-5)


@pytest.mark.unit
def test_collection_request_naive_datetime_raises() -> None:
    naive = datetime.now()
    with pytest.raises(ValueError):
        CollectionRequest(source_id="src_1", mode=CollectionMode.FULL, window_start=naive)
    with pytest.raises(ValueError):
        CollectionRequest(source_id="src_1", mode=CollectionMode.FULL, window_end=naive)


@pytest.mark.unit
def test_collection_result_valid() -> None:
    res_empty = CollectionResult(items=[], next_checkpoint=None, has_more=False)
    assert res_empty.has_more is False

    item = RawSourceItem(source_item_type="post", raw_payload="x")
    res_more = CollectionResult(items=[item], next_checkpoint="next_ckpt", has_more=True)
    assert res_more.has_more is True
    assert res_more.next_checkpoint == "next_ckpt"


@pytest.mark.unit
def test_collection_result_has_more_without_checkpoint_raises() -> None:
    with pytest.raises(ValueError):
        CollectionResult(items=[], next_checkpoint=None, has_more=True)
