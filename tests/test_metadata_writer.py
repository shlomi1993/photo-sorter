from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from photo_sorting.metadata_writer import MetadataWriter


def test_heic_update_uses_exiftool_creates_backup_and_verifies(tmp_path):
    photo = tmp_path / "20260729_135001.heic"
    photo.write_bytes(b"example HEIC payload")
    target = datetime(2026, 7, 29, 13, 50, 1)
    responses = [
        SimpleNamespace(returncode=0, stdout="1 image files updated", stderr=""),
        SimpleNamespace(
            returncode=0,
            stdout='[{"DateTimeOriginal":"2026:07:29 13:50:01"}]',
            stderr="",
        ),
    ]

    writer = MetadataWriter()
    with patch("photo_sorting.metadata_writer.shutil.which", return_value="/usr/bin/exiftool"), patch(
        "photo_sorting.metadata_writer.subprocess.run", side_effect=responses
    ) as run:
        assert writer.update_dates(photo, target, preserve_time=False)

    assert (tmp_path / ".backup" / photo.name).read_bytes() == b"example HEIC payload"
    assert writer.last_update_details == {
        "embedded_metadata": True,
        "filesystem_timestamps": True,
    }
    assert "-EXIF:DateTimeOriginal=2026:07:29 13:50:01" in run.call_args_list[0].args[0]
    assert run.call_count == 2


def test_heic_update_reports_filesystem_only_when_exiftool_fails(tmp_path):
    photo = tmp_path / "photo.heic"
    photo.write_bytes(b"example HEIC payload")
    failure = SimpleNamespace(returncode=1, stdout="", stderr="Invalid metadata")

    writer = MetadataWriter()
    with patch("photo_sorting.metadata_writer.shutil.which", return_value="/usr/bin/exiftool"), patch(
        "photo_sorting.metadata_writer.subprocess.run", return_value=failure
    ):
        assert writer.update_dates(photo, datetime(2026, 7, 29, 13, 50, 1))

    assert writer.last_update_details == {
        "embedded_metadata": False,
        "filesystem_timestamps": True,
    }
