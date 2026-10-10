import sys
from datetime import date, datetime

import pytest
from PIL import Image

from photo_sorting.cli import (
    main,
    extract_date_from_filename,
    extract_date_from_whatsapp_filename,
    extract_date_from_camera_or_whatsapp_filename,
)
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


@pytest.mark.parametrize("filename, expected", [
    ("IMG-20250120-WA0011.jpg", date(2025, 1, 20)),
    ("VID-20260727-WA0017.mp4", date(2026, 7, 27)),
    ("vid-20260727-wa0017(1).MP4", date(2026, 7, 27)),
    ("VID-20260230-WA0017.mp4", None),
    ("img-20250120-wa0011(2).JpG", date(2025, 1, 20)),
    ("20260411_114806.jpg", datetime(2026, 4, 11, 11, 48, 6)),
    ("IMG_20260411_114806(0).heic", datetime(2026, 4, 11, 11, 48, 6)),
    ("DSC_20260411_1148.jpg", datetime(2026, 4, 11, 11, 48)),
    ("PXL_20260411_114806123.jpg", datetime(2026, 4, 11, 11, 48, 6)),
    ("holiday-20260411.jpg", None),
    ("20260411.jpg", None),
    ("IMG_0001.jpg", None),
    ("IMG-20250230-WA0011.jpg", None),
    ("IMG_20260411_254806.jpg", None),
    ("IMG-20250120-WAholiday.jpg", None),
])
def test_automatic_filename_detection(filename, expected):
    assert extract_date_from_camera_or_whatsapp_filename(filename) == expected


def make_jpeg(path):
    Image.new("RGB", (8, 8), color="red").save(path, format="JPEG")


def test_default_cli_updates_mixed_directory_and_skips_other_names(tmp_path, monkeypatch):
    folder = tmp_path / "2020.1.2 - Event"
    folder.mkdir()
    camera = folder / "IMG_20260411_114806.JpG"
    whatsapp = folder / "IMG-20250120-WA0011.jpg"
    unrelated = folder / "holiday-20260411.jpg"
    invalid = folder / "20260411_254806.jpg"
    for photo in (camera, whatsapp, unrelated, invalid):
        make_jpeg(photo)
    untouched = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (unrelated, invalid)}
    # A directory with a matching suffix must not be treated as an image.
    (folder / "20260411_114806.jpg").mkdir()
    monkeypatch.setattr(sys, "argv", ["photo-sorting", str(folder)])
    main()
    assert folder.exists()
    for photo, target in ((camera, datetime(2026, 4, 11, 11, 48, 6)),
                          (whatsapp, datetime(2025, 1, 20, 12))):
        assert MetadataReader().read_dates(photo)["date_taken"] == target
        assert photo.stat().st_mtime == pytest.approx(target.timestamp(), abs=1)
    for photo, original in untouched.items():
        assert (photo.read_bytes(), photo.stat().st_mtime_ns) == original


@pytest.mark.parametrize("filename, dry_run", [
    ("20260411_114806.jpg", False),
    ("IMG-20250120-WA0011.jpg", False),
    ("holiday.jpg", False),
    ("20260411_114806.jpg", True),
])
def test_default_cli_single_image(tmp_path, monkeypatch, filename, dry_run):
    photo = tmp_path / filename
    make_jpeg(photo)
    original = (photo.read_bytes(), photo.stat().st_mtime_ns)
    monkeypatch.setattr(sys, "argv", ["photo-sorting", str(photo)] + (["--dry-run"] if dry_run else []))
    main()
    if dry_run or filename == "holiday.jpg":
        assert (photo.read_bytes(), photo.stat().st_mtime_ns) == original
    else:
        assert MetadataReader().read_dates(photo)["date_taken"] is not None


def test_folder_date_dry_run_reads_original_directory(tmp_path, monkeypatch):
    folder = tmp_path / "2020.1.2 - Event"
    folder.mkdir()
    photo = folder / "holiday.jpg"
    make_jpeg(photo)
    original = photo.read_bytes()
    calls = []
    monkeypatch.setattr(MetadataWriter, "update_dates", lambda self, path, target, **kw: calls.append((path, target)) or False)
    monkeypatch.setattr(sys, "argv", ["photo-sorting", str(folder), "--folder-date", "--dry-run"])
    main()
    assert calls == [(photo, date(2020, 1, 2))]
    assert folder.exists()
    assert photo.read_bytes() == original


def test_whatsapp_mode_recognizes_video_date():
    assert extract_date_from_whatsapp_filename("VID-20260727-WA0017.mp4") == date(2026, 7, 27)


def test_default_cli_processes_whatsapp_video(tmp_path, monkeypatch):
    video = tmp_path / "VID-20260727-WA0017.mp4"
    video.touch()
    calls = []
    monkeypatch.setattr(MetadataWriter, "update_dates", lambda self, path, target, **kw: calls.append((path, target, kw)) or False)
    monkeypatch.setattr(sys, "argv", ["photo-sorting", str(video)])
    main()
    assert len(calls) == 1
    assert calls[0][:2] == (video, date(2026, 7, 27))
    assert calls[0][2]["preserve_time"] is False
