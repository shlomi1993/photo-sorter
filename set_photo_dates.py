import os
import re
import sys
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

def set_file_times(path, date):
    """Set file created/modified times."""
    ts = date.timestamp()
    os.utime(path, (ts, ts))  # access, modified

def set_exif_date(path, date):
    """Update EXIF DateTimeOriginal and DateTime."""
    try:
        img = Image.open(path)
        exif = img.getexif()

        # Map common date fields
        exif_dict = {TAGS.get(tag): tag for tag in exif}
        dt_str = date.strftime("%Y:%m:%d %H:%M:%S")

        if "DateTimeOriginal" in exif_dict:
            exif[exif_dict["DateTimeOriginal"]] = dt_str
        if "DateTime" in exif_dict:
            exif[exif_dict["DateTime"]] = dt_str

        img.save(path, exif=exif)
    except Exception as e:
        print(f"Skipping EXIF update for {path}: {e}")

def process_directory(directory):
    pattern = re.compile(r"IMG-(\d{8})-WA\d+")
    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if not match:
            continue

        date_str = match.group(1)  # e.g. 20230930
        date = datetime.strptime(date_str, "%Y%m%d")

        path = os.path.join(directory, filename)
        print(f"Updating {filename} -> {date.date()}")

        set_file_times(path, date)
        set_exif_date(path, date)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python set_photo_dates.py <directory>")
        sys.exit(1)

    process_directory(sys.argv[1])
