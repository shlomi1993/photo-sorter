"""
Metadata reading module for extracting date information from images and videos.

This module focuses on the most important dates: when photos were taken
and file creation dates for cross-platform compatibility.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

from PIL import Image
from mutagen import File as MutagenFile

# Try to import pyexiv2, but gracefully handle if it's not available
PYEXIV2_AVAILABLE = True
try:
    import pyexiv2
except (ImportError, OSError) as e:
    PYEXIV2_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"pyexiv2 not available: {e}. Will use PIL fallback for metadata reading.")

logger = logging.getLogger(__name__)


class MetadataReader:
    """Class for reading the most important date metadata from media files."""

    def __init__(self):
        """Initialize the metadata reader."""
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}
        self.supported_video_formats = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}

    def read_dates(self, file_path: Union[str, Path]) -> Dict[str, Optional[datetime]]:
        """
        Read the most important date information from a media file.

        Focuses on creation date and taken date as these are the most important
        for photo organization and cross-platform compatibility.

        Args:
            file_path: Path to the media file

        Returns:
            Dictionary containing important date fields:
            - 'date_taken': When photo was actually taken (EXIF DateTimeOriginal)
            - 'file_created': File creation time (OS level)
            - 'file_modified': File modification time (OS level)
        """
        file_path = Path(file_path)
        dates = {
            'date_taken': None,
            'file_created': None,
            'file_modified': None
        }

        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return dates

        # Read file system dates
        try:
            stat = file_path.stat()
            dates['file_modified'] = datetime.fromtimestamp(stat.st_mtime)

            # On some systems, creation time is available
            if hasattr(stat, 'st_birthtime'):  # macOS
                dates['file_created'] = datetime.fromtimestamp(stat.st_birthtime)
            elif hasattr(stat, 'st_ctime'):  # Windows (creation), Unix (change time)
                dates['file_created'] = datetime.fromtimestamp(stat.st_ctime)

        except Exception as e:
            logger.warning(f"Could not read file system dates for {file_path}: {e}")

        file_ext = file_path.suffix.lower()

        # Handle image files - focus on DateTimeOriginal (when taken)
        if file_ext in self.supported_image_formats:
            taken_date = self._read_date_taken(file_path)
            if taken_date:
                dates['date_taken'] = taken_date

        # Handle video files
        elif file_ext in self.supported_video_formats:
            video_date = self._read_video_creation_date(file_path)
            if video_date:
                dates['date_taken'] = video_date

        else:
            logger.warning(f"Unsupported file format: {file_ext}")

        # Log the dates found
        found_dates = {k: v for k, v in dates.items() if v is not None}
        if found_dates:
            logger.debug(f"Found dates in {file_path.name}: {found_dates}")
        else:
            logger.warning(f"No date metadata found in {file_path.name}")

        return dates

    def _read_date_taken(self, file_path: Path) -> Optional[datetime]:
        """Read when the photo was actually taken (EXIF DateTimeOriginal)."""
        # Try pyexiv2 first for better EXIF support
        if PYEXIV2_AVAILABLE:
            try:
                with pyexiv2.Image(str(file_path)) as img:
                    exif_data = img.read_exif()
                    if 'Exif.Photo.DateTimeOriginal' in exif_data:
                        date_str = exif_data['Exif.Photo.DateTimeOriginal']
                        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            except Exception as e:
                logger.debug(f"pyexiv2 failed for {file_path}: {e}")

        # Fallback to PIL
        try:
            with Image.open(file_path) as img:
                if hasattr(img, '_getexif') and img._getexif():
                    exif_data = img._getexif()
                    # DateTimeOriginal tag
                    if 36867 in exif_data:
                        date_str = exif_data[36867]
                        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        except Exception as e:
            logger.debug(f"PIL failed for {file_path}: {e}")

        return None

    def _read_video_creation_date(self, file_path: Path) -> Optional[datetime]:
        """Read video creation time."""
        try:
            file = MutagenFile(file_path)
            if file is None:
                return None

            # Try common creation time fields
            creation_keys = ['creation_time', '©day', 'CREATION_TIME', 'date']

            for key in creation_keys:
                if key in file:
                    try:
                        date_value = file[key]
                        if isinstance(date_value, list) and date_value:
                            date_value = date_value[0]

                        if isinstance(date_value, str):
                            # Try common video date formats
                            formats = [
                                "%Y-%m-%dT%H:%M:%S.%fZ",
                                "%Y-%m-%dT%H:%M:%SZ",
                                "%Y-%m-%d %H:%M:%S",
                                "%Y-%m-%d",
                            ]

                            for fmt in formats:
                                try:
                                    return datetime.strptime(date_value, fmt)
                                except ValueError:
                                    continue
                    except Exception as e:
                        logger.debug(f"Error parsing video date {key}={date_value}: {e}")

        except Exception as e:
            logger.debug(f"Error reading video metadata from {file_path}: {e}")

        return None

    def get_best_date(self, dates: Dict[str, Optional[datetime]]) -> Optional[datetime]:
        """
        Get the most reliable date from the available metadata.

        Priority order:
        1. Date taken (EXIF DateTimeOriginal or video creation time)
        2. File creation time
        3. File modification time

        Args:
            dates: Dictionary of dates as returned by read_dates()

        Returns:
            The best available date, or None if no dates found
        """
        priority_order = [
            'date_taken',
            'file_created',
            'file_modified'
        ]

        for date_key in priority_order:
            if dates.get(date_key):
                logger.debug(f"Selected {date_key} as best date: {dates[date_key]}")
                return dates[date_key]

        logger.warning("No valid dates found")
        return None