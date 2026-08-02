from datetime import date, datetime

from photo_sorting.cli import extract_date_from_filename
from photo_sorting.metadata_reader import MetadataReader
from photo_sorting.metadata_writer import MetadataWriter


def test_extracts_timestamp_from_filename():
    assert extract_date_from_filename("20260411_114806.jpg") == datetime(
        2026, 4, 11, 11, 48, 6
    )


def test_extracts_timestamp_before_duplicate_suffix():
    assert extract_date_from_filename("20260411_114806(0).jpg") == datetime(
        2026, 4, 11, 11, 48, 6
    )


def test_extracts_timestamp_without_seconds():
    assert extract_date_from_filename("20260411_1148.jpg") == datetime(
        2026, 4, 11, 11, 48
    )


def test_date_only_behavior_is_unchanged():
    assert extract_date_from_filename("20260411.jpg") == date(2026, 4, 11)


def test_heic_is_supported_by_metadata_handlers():
    assert ".heic" in MetadataReader().supported_image_formats
    assert ".heic" in MetadataWriter().supported_image_formats
