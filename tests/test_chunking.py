# The chunking tests

import pytest

from src.chunking.splitter import (
    split_document,
    split_documents,
)
from src.ingestion.schema import DocumentRecord


def make_record(text):
    return DocumentRecord(
        text=text,
        source="sample.txt",
        file_name="sample.txt",
        file_type="txt",
        page_number=None,
    )


def test_short_document_produces_one_chunk():
    record = make_record("Hello world")

    chunks = split_document(
        record,
        chunk_size=100,
        chunk_overlap=20,
    )

    assert len(chunks) == 1
    assert chunks[0].text == "Hello world"


def test_long_document_produces_multiple_chunks():
    record = make_record("A" * 1200)

    chunks = split_document(
        record,
        chunk_size=500,
        chunk_overlap=100,
    )

    assert len(chunks) > 1

    assert all(
        len(chunk.text) <= 500
        for chunk in chunks
    )


def test_chunk_overlap():
    record = make_record(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )

    chunks = split_document(
        record,
        chunk_size=10,
        chunk_overlap=3,
    )

    assert chunks[0].text[-3:] == chunks[1].text[:3]


def test_chunk_metadata_preserved():
    record = DocumentRecord(
        text="A" * 800,
        source="policy.pdf",
        file_name="policy.pdf",
        file_type="pdf",
        page_number=3,
    )

    chunks = split_document(record)

    assert all(
        chunk.file_name == "policy.pdf"
        for chunk in chunks
    )

    assert all(
        chunk.page_number == 3
        for chunk in chunks
    )


def test_chunk_ids_are_deterministic():
    record = make_record("A" * 1000)

    first = split_document(record)
    second = split_document(record)

    assert [
        chunk.chunk_id for chunk in first
    ] == [
        chunk.chunk_id for chunk in second
    ]


def test_chunk_ids_are_unique():
    record = make_record("A" * 1000)

    chunks = split_document(record)

    ids = [
        chunk.chunk_id
        for chunk in chunks
    ]

    assert len(ids) == len(set(ids))


def test_empty_document():
    record = make_record("   ")

    chunks = split_document(record)

    assert chunks == []


@pytest.mark.parametrize(
    "chunk_size,chunk_overlap",
    [
        (0, 0),
        (-1, 0),
        (100, -1),
        (100, 100),
        (100, 150),
    ],
)
def test_invalid_chunk_settings(
    chunk_size,
    chunk_overlap,
):
    record = make_record("Example text")

    with pytest.raises(ValueError):
        split_document(
            record,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )


def test_chunk_offsets_match_source():
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 20
    record = make_record(text)

    chunks = split_document(
        record,
        chunk_size=100,
        chunk_overlap=20,
    )

    for chunk in chunks:
        assert (
            text[chunk.start_char:chunk.end_char]
            == chunk.text
        )


def test_split_multiple_documents():
    records = [
        make_record("A" * 600),
        make_record("B" * 600),
    ]

    chunks = split_documents(records)

    assert len(chunks) >= 4