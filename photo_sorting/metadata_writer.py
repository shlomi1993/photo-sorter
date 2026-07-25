"""
Metadata writing module for updating date information in images and videos.

This module provides functionality to update various date fields in media files
to ensure consistency across different platforms and applications.
"""

import os
import shutil
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Union, Optional, TYPE_CHECKING

from mutagen import File as MutagenFile

if TYPE_CHECKING:
    from .metadata_reader import MetadataReader

# Try to import pyexiv2, but gracefully handle if it's not available
PYEXIV2_AVAILABLE = True
PYEXIV2_ERROR = None
try:
    import pyexiv2
except (ImportError, OSError) as e:
    PYEXIV2_AVAILABLE = False
    PYEXIV2_ERROR = str(e)

logger = logging.getLogger(__name__)


class MetadataWriter:
    """Class for writing date metadata to various media file types."""

    def __init__(self, dry_run: bool = False, backup: bool = False, backup_dir: Optional[str] = None):
        """
        Initialize the metadata writer.

        Args:
            dry_run: If True, show what would be changed without making modifications
            backup: If True, create backup files before modifying
            backup_dir: Name of the backup directory to create/use (if None, no backups)
        """
        self.dry_run = dry_run
        self.backup = backup
        self.backup_dir = backup_dir
        self.supported_image_formats = {'.jpg', '.jpeg', '.tiff', '.tif'}
        self.supported_video_formats = {'.mp4', '.mov', '.m4v'}

        if dry_run:
            logger.info("Running in DRY RUN mode - no files will be modified")

    def update_dates(self, file_path: Union[str, Path], target_date: Union[date, datetime],
                     preserve_time: bool = True, metadata_reader: Optional['MetadataReader'] = None) -> bool:
        """
        Update all relevant date fields in a media file.

        Args:
            file_path: Path to the media file
            target_date: Date to set (if date object, time will be set to noon unless preserve_time=True)
            preserve_time: If True and metadata_reader provided, preserve existing time from file
            metadata_reader: MetadataReader instance to read existing time from file

        Returns:
            True if update was successful, False otherwise
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return False

        # Convert date to datetime, preserving existing time if possible
        if isinstance(target_date, date) and not isinstance(target_date, datetime):
            existing_time = None

            # Try to get existing time from metadata if preserve_time is True
            if preserve_time and metadata_reader:
                try:
                    existing_dates = metadata_reader.read_dates(file_path)
                    # Prefer date_taken, then file_created, then file_modified
                    for date_type in ['date_taken', 'file_created', 'file_modified']:
                        if existing_dates.get(date_type):
                            existing_time = existing_dates[date_type].time()
                            logger.debug(f"Preserving time {existing_time} from {date_type}")
                            break
                except Exception as e:
                    logger.debug(f"Could not read existing time from {file_path}: {e}")

            # Use existing time if found, otherwise default to noon
            if existing_time:
                target_datetime = datetime.combine(target_date, existing_time)
            else:
                target_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=12))
        else:
            target_datetime = target_date

        logger.info(f"Updating dates in {file_path.name} to {target_datetime}")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would update {file_path.name}")
            return True

        # Create backup if requested
        if self.backup:
            if not self._create_backup(file_path):
                logger.error(f"Failed to create backup for {file_path}")
                return False

        file_ext = file_path.suffix.lower()

        success = False

        # Handle image files
        if file_ext in self.supported_image_formats:
            success = self._update_image_dates(file_path, target_datetime)

        # Handle video files
        elif file_ext in self.supported_video_formats:
            success = self._update_video_dates(file_path, target_datetime)

        else:
            logger.warning(f"Unsupported file format for metadata writing: {file_ext}")

        # Always try to update file system timestamps as fallback
        if self._update_file_timestamps(file_path, target_datetime):
            success = True

        return success

    def reset_file_dates_to_exif(self, file_path: Union[str, Path], metadata_reader: 'MetadataReader') -> bool:
        """
        Reset file creation and modification dates to match the original EXIF date taken from the photo.

        Args:
            file_path: Path to the media file
            metadata_reader: MetadataReader instance to read the original EXIF data

        Returns:
            bool: True if successful, False otherwise
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return False

        try:
            # Read the original EXIF date from the photo
            metadata_dates = metadata_reader.read_dates(file_path)

            # Use date_taken as the source of truth for the reset
            original_date = metadata_dates.get('date_taken')

            if not original_date:
                logger.warning(f"No EXIF date found in {file_path.name}, cannot reset filesystem dates")
                return False

            logger.info(f"Resetting file timestamps for {file_path.name} to original EXIF date: {original_date}")

            if self.dry_run:
                logger.info(f"[DRY RUN] Would reset timestamps for {file_path.name} to {original_date}")
                return True

            # Create backup if requested
            if self.backup:
                if not self._create_backup(file_path):
                    logger.error(f"Failed to create backup for {file_path}")
                    return False

            # Reset the file system timestamps to match the original EXIF date
            success = self._update_file_timestamps(file_path, original_date)

            if success:
                logger.info(f"✓ Reset file timestamps for {file_path.name}")
            else:
                logger.error(f"✗ Failed to reset file timestamps for {file_path.name}")

            return success

        except Exception as e:
            logger.error(f"Error resetting file dates for {file_path.name}: {e}")
            return False

    def _create_backup(self, file_path: Path) -> bool:
        """Create a backup of the original file in the specified backup directory."""
        try:
            # Use custom backup directory name if provided, otherwise use '.backup'
            backup_dir_name = self.backup_dir if self.backup_dir else '.backup'
            backup_dir = file_path.parent / backup_dir_name
            backup_dir.mkdir(exist_ok=True)

            backup_path = backup_dir / file_path.name

            # Don't create backup if one already exists
            if backup_path.exists():
                logger.debug(f"Backup already exists: {backup_path}")
                return True

            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return False

    def _update_image_dates(self, file_path: Path, target_datetime: datetime) -> bool:
        """Update date metadata in image files."""
        success = False

        # Format datetime for EXIF (YYYY:MM:DD HH:MM:SS)
        exif_datetime_str = target_datetime.strftime("%Y:%m:%d %H:%M:%S")

        # Try updating with pyexiv2 first (preferred method)
        if PYEXIV2_AVAILABLE:
            try:
                success = self._update_with_pyexiv2(file_path, exif_datetime_str)
                if success:
                    logger.debug(f"Successfully updated EXIF data using pyexiv2 for {file_path.name}")
                else:
                    logger.warning(f"pyexiv2 failed to update EXIF data for {file_path.name}")
            except Exception as e:
                logger.warning(f"pyexiv2 update failed for {file_path.name}: {e}")
        else:
            # Only show this warning once per session, not for every file
            if not hasattr(self, '_pyexiv2_warning_shown'):
                logger.warning(f"pyexiv2 not available ({PYEXIV2_ERROR}). EXIF metadata updates will be skipped.")
                logger.info("To enable EXIF updates, install pyexiv2: pip install pyexiv2")
                self._pyexiv2_warning_shown = True
            logger.debug(f"Skipping EXIF update for {file_path.name} (pyexiv2 not available)")

        # Note: We could try other methods like PIL for basic EXIF writing,
        # but pyexiv2 is the most reliable for writing EXIF data while preserving image quality
        # and supporting the full range of EXIF fields.

        return success

    def _update_with_pyexiv2(self, file_path: Path, exif_datetime_str: str) -> bool:
        """Update image metadata using pyexiv2."""
        if not PYEXIV2_AVAILABLE:
            return False

        try:
            with pyexiv2.Image(str(file_path)) as img:
                # Read existing metadata to preserve non-date fields
                exif_dict = img.read_exif()

                # Focus on the most important date field for cross-platform compatibility
                date_tags = {
                    'Exif.Photo.DateTimeOriginal': exif_datetime_str,  # When photo was taken - most important
                    'Exif.Image.DateTime': exif_datetime_str,          # General date/time - widely supported
                }

                # Update the metadata
                exif_dict.update(date_tags)
                img.modify_exif(exif_dict)

                logger.debug(f"Updated EXIF dates in {file_path.name}: {exif_datetime_str}")
                return True

        except Exception as e:
            logger.error(f"pyexiv2 error updating {file_path}: {e}")
            return False

    def _update_video_dates(self, file_path: Path, target_datetime: datetime) -> bool:
        """
        Update date metadata in video files.

        Note: Video metadata writing is more limited and format-dependent.
        Many video players rely on file system timestamps rather than embedded metadata.
        """
        success = False

        try:
            file = MutagenFile(file_path, easy=False)

            if file is None:
                logger.warning(f"Mutagen could not open {file_path} for writing")
                return False

            # ISO format for video metadata
            iso_datetime_str = target_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

            # Try to set creation time (format varies by container)
            if hasattr(file, 'tags') and file.tags is not None:
                # For MP4 files
                if 'mp4' in str(type(file)).lower():
                    # MP4 uses specific atom structure
                    try:
                        file.tags['creation_time'] = iso_datetime_str
                        file.save()
                        success = True
                        logger.debug(f"Updated MP4 creation_time in {file_path.name}")
                    except Exception as e:
                        logger.debug(f"Could not update MP4 metadata: {e}")

                # For other formats, try common fields
                else:
                    date_fields = ['date', 'creation_time', 'CREATION_TIME']
                    for field in date_fields:
                        try:
                            file.tags[field] = iso_datetime_str
                            file.save()
                            success = True
                            logger.debug(f"Updated {field} in {file_path.name}")
                            break
                        except Exception as e:
                            logger.debug(f"Could not update {field}: {e}")
                            continue

        except Exception as e:
            logger.warning(f"Error updating video metadata in {file_path}: {e}")

        return success

    def _update_file_timestamps(self, file_path: Path, target_datetime: datetime) -> bool:
        """
        Update file system timestamps.

        This is important because many applications fall back to file timestamps
        when embedded metadata is not available or reliable.
        """
        try:
            # Convert datetime to timestamp
            timestamp = target_datetime.timestamp()

            # Update modification time and access time
            os.utime(file_path, (timestamp, timestamp))

            logger.debug(f"Updated file timestamps for {file_path.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update file timestamps for {file_path}: {e}")
            return False

    def restore_from_backup(self, file_path: Union[str, Path]) -> bool:
        """
        Restore a file from its backup in the specified backup directory.

        Args:
            file_path: Path to the original file

        Returns:
            True if restore was successful, False otherwise
        """
        file_path = Path(file_path)
        backup_dir_name = self.backup_dir if self.backup_dir else '.backup'
        backup_dir = file_path.parent / backup_dir_name
        backup_path = backup_dir / file_path.name

        if not backup_path.exists():
            logger.error(f"No backup found for {file_path} in {backup_dir}")
            return False

        try:
            shutil.copy2(backup_path, file_path)
            logger.info(f"Restored {file_path.name} from backup")
            return True

        except Exception as e:
            logger.error(f"Failed to restore {file_path} from backup: {e}")
            return False

    def cleanup_backups(self, directory: Union[str, Path], backup_dir_name: Optional[str] = None) -> int:
        """
        Remove the backup directory and all its contents.

        Args:
            directory: Directory containing the backup folder to clean up
            backup_dir_name: Name of the backup directory (if None, uses instance backup_dir or '.backup')

        Returns:
            Number of backup files removed
        """
        directory = Path(directory)
        if backup_dir_name is None:
            backup_dir_name = self.backup_dir if self.backup_dir else '.backup'
        backup_dir = directory / backup_dir_name

        if not backup_dir.exists():
            logger.debug(f"No {backup_dir_name} directory found in {directory}")
            return 0

        try:
            backup_files = list(backup_dir.glob("*"))
            removed_count = len(backup_files)

            # Remove the entire backup directory
            shutil.rmtree(backup_dir)

            if removed_count > 0:
                logger.info(f"Removed {backup_dir_name} directory with {removed_count} files from {directory}")

            return removed_count

        except Exception as e:
            logger.error(f"Failed to remove {backup_dir_name} directory from {directory}: {e}")
            return 0

    def get_platform_compatibility_info(self) -> dict:
        """
        Get information about which metadata fields are supported on different platforms.

        Returns:
            Dictionary with platform compatibility information
        """
        return {
            "cross_platform_reliable": [
                "EXIF DateTimeOriginal",
                "EXIF DateTimeDigitized",
                "File modification time"
            ],
            "windows": [
                "File creation time",
                "EXIF DateTime",
                "Windows Media metadata"
            ],
            "macos": [
                "File birth time",
                "Extended attributes",
                "Spotlight metadata"
            ],
            "linux": [
                "File modification time",
                "Extended attributes (ext4)"
            ],
            "android": [
                "EXIF DateTimeOriginal",
                "MediaStore database"
            ],
            "notes": {
                "exif_priority": "EXIF DateTimeOriginal is the most universally supported",
                "file_timestamps": "File system timestamps are always available but can be modified easily",
                "video_limitations": "Video metadata writing support varies greatly by format and player"
            }
        }
