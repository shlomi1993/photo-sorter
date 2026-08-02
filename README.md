# 📸 Photo Sorting

A command-line tool for correcting photo and video dates from folder names,
explicit dates, filenames, or existing EXIF metadata.

## ✨ Features

- Process a directory or a single media file.
- Read dates from event folders such as `2025.04.11 - Event Name`.
- Read dates and times from filenames such as:
  - `20260411_114806.jpg`
  - `20260411_114806(0).jpg`
  - `IMG-20250120-WA0011.jpg`
- Update image EXIF metadata, supported video metadata, and filesystem
  timestamps.
- Preview operations with `--dry-run`.
- Optionally create backups before modifying files.
- Handle Hebrew and other Unicode paths.

## 📋 Requirements

- Python 3.8 or newer
- Pillow
- Mutagen
- Colorama
- `pyexiv2` for reading and writing EXIF metadata
- ExifTool for safe, verified HEIC metadata updates (`brew install exiftool` on macOS)

## 📦 Installation

Clone the repository and run the installer:

```bash
git clone https://github.com/shlomi1993/photo-sorter.git
cd photo-sorting
./install.sh
```

For development, create a virtual environment and install the package in
editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 🚀 Usage

The positional argument can be an event directory or one supported media file:

```bash
photo-sorting PATH [OPTIONS]
```

### Parse the date and time from filenames

```bash
photo-sorting "/path/to/photos" --by-name
```

For `20260411_114806.jpg`, this sets the timestamp to
`2026-04-11 11:48:06`. If a filename contains only a date, the default time is
noon.

Preview changes first:

```bash
photo-sorting "/path/to/photos" --by-name --dry-run --verbose
```

### Use the event-folder date

For a directory named `2025.04.11 - Event Name`:

```bash
photo-sorting "/path/to/2025.04.11 - Event Name"
```

This changes the date while preserving an existing time when possible.

### Supply a date explicitly

```bash
photo-sorting "/path/to/photos" --date 2025.04.11
```

### Process WhatsApp filenames

```bash
photo-sorting "/path/to/photos" --whatsapp
```

This supports names such as `IMG-20250120-WA0011.jpg`. WhatsApp mode stops if
existing EXIF date-taken metadata is found.

### Reset filesystem dates from EXIF

```bash
photo-sorting "/path/to/photos" --reset
```

### Create backups

```bash
photo-sorting "/path/to/photos" --by-name --backup-dir originals
```

## ⚙️ Options

| Option | Description |
| --- | --- |
| `--date`, `-d` | Use an explicit date in `YYYY.MM.DD` format |
| `--by-name` | Parse an individual date, and time when available, from each filename |
| `--whatsapp` | Process `IMG-YYYYMMDD-WA*` filenames |
| `--reset` | Reset filesystem timestamps from existing EXIF data |
| `--dry-run` | Report changes without modifying files |
| `--verbose`, `-v` | Enable verbose logging |
| `--backup-dir NAME` | Back up files before modifying them |
| `--help`, `-h` | Show command help |

## 🎞️ Supported media

The CLI discovers JPEG, PNG, TIFF, BMP, HEIC, MP4, MOV, AVI, MKV, WMV, FLV,
and WebM files. Metadata-writing support varies by format and the installed
Exiv2 build; filesystem timestamps provide the fallback.

HEIC writes use ExifTool, automatically create a safety copy in `.backup`
(or the directory selected with `--backup-dir`), and verify the embedded
`DateTimeOriginal` value after writing. The tool never ignores metadata errors
or removes ICC color profiles automatically.

## 🛡️ Safety

Run with `--dry-run` before processing a large collection:

```bash
photo-sorting "/path/to/photos" --by-name --dry-run
```

Use `--backup-dir` when changing irreplaceable media. Cloud-synced folders may
propagate timestamp and metadata changes to other devices.

## 🧪 Development

Run the tests with:

```bash
python -m pytest
```

## 📄 License

This project is licensed under the terms in [LICENSE](LICENSE).
