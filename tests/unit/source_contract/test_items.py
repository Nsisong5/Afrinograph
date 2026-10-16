from __future__ import annotations

from datetime import UTC, datetime
import pytest

from afrinograph.modules.source_contract.domain.items import RawSourceItem


@pytest.mark.unit
def test_raw_source_item_valid_construction() -> None:
    item = RawSourceItem(
        source_item_id="123",
        source_item_type="post",
        title="Title",
        content_text="Content",
        original_url="https://example.com",
        raw_payload=b"raw",
        provider_metadata={"key": "val"},
        source_published_at=datetime.now(UTC),
        retrieved_at=datetime.now(UTC),
    )
    assert item.source_item_id == "123"
    assert item.source_item_type == "post"
    assert item.title == "Title"
    assert item.content_text == "Content"
    assert item.provider_metadata["key"] == "val"


@pytest.mark.unit
def test_raw_source_item_empty_type_raises() -> None:
    with pytest.raises(ValueError):
        RawSourceItem(source_item_type="", raw_payload="x")


@pytest.mark.unit
def test_raw_source_item_empty_id_raises() -> None:
    with pytest.raises(ValueError):
        RawSourceItem(source_item_id="", source_item_type="post", raw_payload="x")


@pytest.mark.unit
def test_raw_source_item_empty_payload_raises() -> None:
    with pytest.raises(ValueError):
        RawSourceItem(source_item_type="post", raw_payload="")


@pytest.mark.unit
def test_raw_source_item_naive_datetime_raises() -> None:
    naive_dt = datetime.now()
    with pytest.raises(ValueError):
        RawSourceItem(source_item_type="post", raw_payload="x", source_published_at=naive_dt)
    with pytest.raises(ValueError):
        RawSourceItem(source_item_type="post", raw_payload="x", retrieved_at=naive_dt)


@pytest.mark.unit
def test_raw_source_item_non_json_metadata_raises() -> None:
    with pytest.raises(ValueError):
        RawSourceItem(source_item_type="post", raw_payload="x", provider_metadata={"bad": object()})


@pytest.mark.unit
def test_raw_source_item_metadata_immutable() -> None:
    item = RawSourceItem(source_item_type="post", raw_payload="x", provider_metadata={"a": 1})
    with pytest.raises(TypeError):
        item.provider_metadata["b"] = 2  # type: ignore[index]


@pytest.mark.unit
def test_raw_source_item_title_content_empty_vs_none() -> None:
    item_none = RawSourceItem(source_item_type="post", raw_payload="x", title=None, content_text=None)
    assert item_none.title is None
    assert item_none.content_text is None

    item_empty = RawSourceItem(source_item_type="post", raw_payload="x", title="", content_text="")
    assert item_empty.title == ""
    assert item_empty.content_text == ""
