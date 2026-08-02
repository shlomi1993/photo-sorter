#!/usr/bin/env python3
"""
Main script for the Photo Sorting Tool.

This script processes a directory of photos/videos and ensures their metadata dates match the expected date extracted
from the directory name.
"""

import argparse
import sys
import re

from pathlib import Path
from datetime import datetime

from photo_sorting import (
    extract_date_from_directory,
    standardize_folder_name,
    MetadataReader,
    MetadataWriter,
    setup_logger
)


def log_update_outcome(logger, writer, file_path: Path, target_date) -> bool:
    """Log whether embedded metadata or only filesystem timestamps changed."""
    details = writer.last_update_details
    embedded = details['embedded_metadata']
    filesystem = details['filesystem_timestamps']

    if embedded and filesystem:
        logger.info(f"  ✓ Updated embedded metadata and filesystem timestamps for {file_path.name} to {target_date}")
    elif embedded:
        logger.warning(f"  ⚠️  Updated embedded metadata for {file_path.name}, but filesystem timestamps failed")
    else:
        logger.warning(
            f"  ⚠️  Embedded metadata was not updated for {file_path.name}; "
            "filesystem timestamps only were updated"
        )

    return embedded


def extract_date_from_whatsapp_filename(filename: str) -> datetime:
    """
    Extract date from WhatsApp filename format (IMG-YYYYMMDD-WA*).

    Args:
        filename (str): The filename to parse.

    Returns:
        Optional[date]: The extracted date, or None if parsing fails.
    """
    # Match WhatsApp pattern: IMG-YYYYMMDD-WA*
    match = re.match(r'IMG-(\d{4})(\d{2})(\d{2})-WA.*', filename)
    if match:
        year, month, day = match.groups()
        try:
            return datetime.strptime(f"{year}{month}{day}", "%Y%m%d").date()
        except ValueError:
            return None
    return None


def extract_date_from_filename(filename: str) -> datetime:
    """
    Extract date from various filename formats.

    Supports formats like:
    - YYYY-MM-DD, YYYY_MM_DD, YYYYMMDD
    - DD-MM-YYYY, DD_MM_YYYY
    - IMG-YYYYMMDD-*, DSC_YYYYMMDD, etc.

    Args:
        filename (str): The filename to parse.

    Returns:
        Optional[date]: The extracted date, or None if parsing fails.
    """
    # Remove file extension
    name_without_ext = filename.rsplit('.', 1)[0]

    # Try various date patterns
    patterns = [
        # ISO format variations
        r'(\d{4})[_-](\d{2})[_-](\d{2})',  # YYYY-MM-DD or YYYY_MM_DD
        r'(\d{4})(\d{2})(\d{2})',          # YYYYMMDD

        # European format variations
        r'(\d{2})[_-](\d{2})[_-](\d{4})',  # DD-MM-YYYY or DD_MM_YYYY

        # Camera/phone formats
        r'IMG[_-](\d{4})(\d{2})(\d{2})',   # IMG-YYYYMMDD or IMG_YYYYMMDD
        r'DSC[_-](\d{4})(\d{2})(\d{2})',   # DSC-YYYYMMDD or DSC_YYYYMMDD
        r'VID[_-](\d{4})(\d{2})(\d{2})',   # VID-YYYYMMDD or VID_YYYYMMDD
        r'(\d{4})[_-](\d{2})[_-](\d{2})[_-]',  # YYYY-MM-DD- (with trailing separator)

        # Timestamp formats
        r'(\d{4})(\d{2})(\d{2})[_-]\d{6}', # YYYYMMDD_HHMMSS
    ]

    for pattern in patterns:
        match = re.search(pattern, name_without_ext)
        if match:
            groups = match.groups()

            # Determine if it's YYYY-MM-DD or DD-MM-YYYY format
            if len(groups[0]) == 4:  # First group is year
                year, month, day = groups[0], groups[1], groups[2]
            else:  # First group is day (DD-MM-YYYY format)
                day, month, year = groups[0], groups[1], groups[2]

            try:
                return datetime.strptime(f"{year}{month}{day}", "%Y%m%d").date()
            except ValueError:
                continue  # Try next pattern

    return None


def main():
    """
    Main entry point for the photo sorting tool.
    """
    parser = argparse.ArgumentParser(
        description="Fix photo/video metadata dates based on directory naming convention"
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to the event folder containing photos/videos or a single file"
    )
    parser.add_argument(
        "--date",
        "-d",
        type=str,
        help="Expected date in YYYY.MM.DD format (if not provided, will extract from folder name)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making actual modifications"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--backup-dir",
        type=str,
        help="Create backup directory with the specified name before modifying files (default: no backups)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset file creation and modification dates to match original EXIF date from photos"
    )
    parser.add_argument(
        "--whatsapp",
        action="store_true",
        help="Process WhatsApp files (IMG-YYYYMMDD-WA*) and extract dates from filenames. Stops if EXIF data exists."
    )
    parser.add_argument(
        "--by-name",
        action="store_true",
        help="Parse date from filename and set as file taken, creation, and modification dates. Skips files with unparseable names."
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logger(verbose=args.verbose)

    try:
        # Validate path exists
        path = Path(args.path)
        if not path.exists():
            logger.error(f"Path does not exist: {path}")
            sys.exit(1)

        # Handle single file vs directory
        if path.is_file():
            # Single file mode
            folder_path = path.parent
            single_file = path
            logger.info(f"Processing single file: {path}")
        elif path.is_dir():
            # Directory mode
            folder_path = path
            single_file = None
            logger.info(f"Processing directory: {path}")
        else:
            logger.error(f"Path is neither a file nor a directory: {path}")
            sys.exit(1)

        # Only standardize folder names when processing directories
        if single_file is None:
            # Check if folder name needs standardization (YYYY.M.D -> YYYY.MM.DD)
            standardized_name = standardize_folder_name(folder_path.name)
            if standardized_name:
                new_folder_path = folder_path.parent / standardized_name
                logger.info(f"Standardizing folder name: {folder_path.name} -> {standardized_name}")

                if not args.dry_run:
                    try:
                        folder_path.rename(new_folder_path)
                        folder_path = new_folder_path
                        logger.info(f"✓ Folder renamed to: {folder_path}")
                    except OSError as e:
                        logger.error(f"Failed to rename folder: {e}")
                        sys.exit(1)
                else:
                    logger.info(f"[DRY RUN] Would rename folder to: {new_folder_path}")
                    # For dry run, use the new path for further processing
                    folder_path = new_folder_path

        # Extract or use provided date (only needed for standard modes)
        expected_date = None
        if args.reset:
            # In reset mode, we don't need a date since we're using EXIF dates
            logger.info("Reset mode: Will use EXIF dates from each file")
        elif args.whatsapp:
            # In WhatsApp mode, we extract dates from individual filenames
            logger.info("WhatsApp mode: Will extract dates from filenames")
        elif args.by_name:
            # In by-name mode, we extract dates from individual filenames
            logger.info("By-name mode: Will extract dates from filenames")
        elif args.date:
            expected_date = datetime.strptime(args.date, "%Y.%m.%d").date()
            logger.info(f"Using provided date: {expected_date}")
        else:
            expected_date = extract_date_from_directory(folder_path.name)
            if not expected_date:
                logger.error(f"Could not extract date from folder name: {folder_path.name}")
                sys.exit(1)
            logger.info(f"Extracted date from folder name: {expected_date}")

        # Initialize metadata handlers
        reader = MetadataReader()
        writer = MetadataWriter(dry_run=args.dry_run, backup=bool(args.backup_dir), backup_dir=args.backup_dir)

        # Process media files
        media_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.heic',
                          '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}

        if single_file:
            # Single file mode - check if it's a supported media file
            if single_file.suffix.lower() in media_extensions:
                media_files = [single_file]
            else:
                logger.error(f"File type not supported: {single_file.suffix}")
                sys.exit(1)
        else:
            # Directory mode - find all media files
            media_files = []
            for ext in media_extensions:
                media_files.extend(folder_path.glob(f"*{ext}"))
                media_files.extend(folder_path.glob(f"*{ext.upper()}"))

        if not media_files:
            if single_file:
                logger.error(f"File is not a supported media type: {single_file}")
            else:
                logger.warning(f"No media files found in folder: {folder_path}")
            return

        logger.info(f"Found {len(media_files)} media files to process")

        processed_count = 0
        modified_count = 0
        embedded_modified_count = 0
        filesystem_only_count = 0

        for file_path in media_files:
            logger.info(f"Processing: {file_path.name}")

            try:
                if args.reset:
                    # Reset mode: Update filesystem dates to match EXIF data
                    if writer.reset_file_dates_to_exif(file_path, reader):
                        modified_count += 1
                        logger.info(f"  ✓ Reset filesystem dates for {file_path.name}")
                    else:
                        logger.info(f"  ✓ No reset needed for {file_path.name}")
                elif args.whatsapp:
                    # WhatsApp mode: Extract date from filename and check for existing EXIF
                    whatsapp_date = extract_date_from_whatsapp_filename(file_path.name)
                    if not whatsapp_date:
                        logger.error(f"  ✗ Could not extract date from WhatsApp filename: {file_path.name}")
                        logger.error("Expected format: IMG-YYYYMMDD-WA*")
                        sys.exit(1)

                    logger.info(f"  Extracted date from filename: {whatsapp_date}")

                    # Check if file already has EXIF date_taken data
                    metadata_dates = reader.read_dates(file_path)
                    if metadata_dates.get('date_taken'):
                        logger.warning(f"  ⚠️  File {file_path.name} already has EXIF date_taken: {metadata_dates['date_taken']}")
                        logger.error("WhatsApp mode stopped - found existing EXIF data")
                        sys.exit(1)

                    # Update dates to the extracted WhatsApp date
                    if writer.update_dates(file_path, whatsapp_date, preserve_time=False, metadata_reader=reader):
                        modified_count += 1
                        if log_update_outcome(logger, writer, file_path, whatsapp_date):
                            embedded_modified_count += 1
                        else:
                            filesystem_only_count += 1
                    else:
                        logger.error(f"  ✗ Failed to update metadata for {file_path.name}")
                elif args.by_name:
                    # By-name mode: Extract date from filename and update metadata
                    filename_date = extract_date_from_filename(file_path.name)
                    if not filename_date:
                        logger.info(f"  ⚠️  Could not extract date from filename: {file_path.name} - skipping")
                        continue

                    logger.info(f"  Extracted date from filename: {filename_date}")

                    # Update dates to the extracted date
                    if writer.update_dates(file_path, filename_date, preserve_time=False, metadata_reader=reader):
                        modified_count += 1
                        if log_update_outcome(logger, writer, file_path, filename_date):
                            embedded_modified_count += 1
                        else:
                            filesystem_only_count += 1
                    else:
                        logger.error(f"  ✗ Failed to update metadata for {file_path.name}")
                else:
                    # Normal mode: Update metadata dates to match expected date
                    metadata_dates = reader.read_dates(file_path)

                    # Check if any dates need updating
                    needs_update = False
                    for date_type, current_date in metadata_dates.items():
                        if current_date and current_date.date() != expected_date:
                            logger.info(f"  {date_type}: {current_date.date()} -> {expected_date}")
                            needs_update = True
                        elif current_date:
                            logger.debug(f"  {date_type}: {current_date.date()} (OK)")
                        else:
                            logger.info(f"  {date_type}: Not set -> {expected_date}")
                            needs_update = True

                    if needs_update:
                        if writer.update_dates(file_path, expected_date, preserve_time=True, metadata_reader=reader):
                            modified_count += 1
                            if log_update_outcome(logger, writer, file_path, expected_date):
                                embedded_modified_count += 1
                            else:
                                filesystem_only_count += 1
                        else:
                            logger.error(f"  ✗ Failed to update metadata for {file_path.name}")
                    else:
                        logger.info(f"  ✓ No changes needed for {file_path.name}")

                processed_count += 1

            except Exception as e:
                logger.error(f"  ✗ Error processing {file_path.name}: {e}")
                continue

        # Summary
        logger.info(f"\nProcessing complete:")
        logger.info(f"  Files processed: {processed_count}")
        logger.info(f"  Files modified: {modified_count}")
        logger.info(f"  Embedded metadata updated: {embedded_modified_count}")
        logger.info(f"  Filesystem timestamps only: {filesystem_only_count}")

        if args.dry_run:
            logger.info("  (Dry run - no actual changes made)")

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
