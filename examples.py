#!/usr/bin/env python3
"""
Example usage scripts for the Photo Sorting Tool.

This file demonstrates various ways to use the photo sorting tool
in different scenarios.
"""

import tempfile
from datetime import date
from pathlib import Path

from photo_sorting import extract_date_from_directory, MetadataReader, MetadataWriter, setup_logger


def example_1_basic_usage():
    """Example 1: Basic usage with a single directory."""
    print("=== Example 1: Basic Usage ===")

    # Setup logging
    logger = setup_logger(verbose=True)

    # Example directory name from your photo collection
    directory_name = "2020.1.2 - אחרי בוחן אמצע באינפי"

    # Extract date from directory name
    extracted_date = extract_date_from_directory(directory_name)
    print(f"Extracted date: {extracted_date}")

    # This is how you would use it with a real directory:
    """
    directory_path = Path("/path/to/your/photos/2020/2020.1.2 - אחרי בוחן אמצע באינפי")

    # Initialize metadata handlers
    reader = MetadataReader()
    writer = MetadataWriter(dry_run=False, backup=True)  # Remove dry_run=False to actually modify files

    # Find all media files
    media_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp',
                       '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}

    media_files = []
    for ext in media_extensions:
        media_files.extend(directory_path.glob(f"*{ext}"))
        media_files.extend(directory_path.glob(f"*{ext.upper()}"))

    for file_path in media_files:
        print(f"Processing: {file_path.name}")

        # Read current metadata
        metadata = reader.read_dates(file_path)

        # Update if needed
        needs_update = any(
            (current_date and current_date.date() != extracted_date) or not current_date
            for current_date in metadata.values() if current_date is not None
        )

        if needs_update:
            success = writer.update_dates(file_path, extracted_date)
            print(f"  Updated: {'Success' if success else 'Failed'}")
        else:
            print(f"  No changes needed")
    """


def example_2_batch_processing():
    """Example 2: Batch processing multiple event directories."""
    print("\n=== Example 2: Batch Processing ===")

    logger = setup_logger(verbose=False)  # Less verbose for batch processing

    # Example: process all events in a year directory
    """
    year_directory = Path("/path/to/your/photos/2023")

    reader = MetadataReader()
    writer = MetadataWriter(dry_run=True, backup=True)  # Use dry_run=True for testing

    # Find all event directories
    event_dirs = [d for d in year_directory.iterdir() if d.is_dir()]

    total_processed = 0
    total_modified = 0

    for event_dir in event_dirs:
        print(f"Processing event: {event_dir.name}")

        # Extract expected date
        expected_date = extract_date_from_directory(event_dir.name)
        if not expected_date:
            print(f"  Skipping - could not extract date from: {event_dir.name}")
            continue

        # Find media files
        media_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.mp4', '.mov']:
            media_files.extend(event_dir.glob(f"*{ext}"))
            media_files.extend(event_dir.glob(f"*{ext.upper()}"))

        print(f"  Found {len(media_files)} media files")

        for media_file in media_files:
            try:
                metadata = reader.read_dates(media_file)

                # Check if update needed
                needs_update = False
                for date_type, current_date in metadata.items():
                    if current_date and current_date.date() != expected_date:
                        needs_update = True
                        break
                    elif not current_date:
                        needs_update = True
                        break

                if needs_update:
                    success = writer.update_dates(media_file, expected_date)
                    if success:
                        total_modified += 1

                total_processed += 1

            except Exception as e:
                print(f"    Error processing {media_file.name}: {e}")

    print(f"\\nBatch processing complete:")
    print(f"  Total files processed: {total_processed}")
    print(f"  Total files modified: {total_modified}")
    """


def example_3_selective_updating():
    """Example 3: Selective updating based on metadata confidence."""
    print("\n=== Example 3: Selective Updating ===")

    """
    This example shows how to be more selective about which dates to update,
    preserving high-confidence metadata while fixing obviously wrong dates.
    """

    logger = setup_logger(verbose=True)

    """
    directory_path = Path("/path/to/photos/2022.7.4 - Independence Day")
    expected_date = extract_date_from_directory(directory_path.name)

    reader = MetadataReader()
    writer = MetadataWriter(dry_run=False, backup=True)

    for file_path in directory_path.glob("*.jpg"):
        metadata = reader.read_dates(file_path)

        # Get the best available date
        best_date = reader.get_best_date(metadata)

        if best_date:
            date_diff = abs((best_date.date() - expected_date).days)

            if date_diff > 7:  # More than a week difference
                print(f"{file_path.name}: Date differs by {date_diff} days")
                print(f"  Current: {best_date.date()}")
                print(f"  Expected: {expected_date}")

                # Ask for confirmation or use automatic rules
                if date_diff > 365:  # More than a year - likely wrong
                    print("  Large difference detected - updating automatically")
                    writer.update_dates(file_path, expected_date)
                else:
                    print("  Moderate difference - manual review recommended")
            else:
                print(f"{file_path.name}: Date looks correct ({best_date.date()})")
        else:
            print(f"{file_path.name}: No date metadata - adding expected date")
            writer.update_dates(file_path, expected_date)
    """


def example_4_metadata_inspection():
    """Example 4: Inspecting metadata without making changes."""
    print("\n=== Example 4: Metadata Inspection ===")

    """
    Use this approach to understand what metadata is present in your files
    before deciding how to proceed with updates.
    """

    logger = setup_logger(verbose=True)

    """
    directory_path = Path("/path/to/photos/2023.5.15 - Event")

    reader = MetadataReader()

    print("Metadata Analysis Report")
    print("=" * 40)

    metadata_summary = {
        'files_with_exif_original': 0,
        'files_with_exif_any': 0,
        'files_with_file_dates_only': 0,
        'files_with_no_dates': 0,
        'date_mismatches': 0
    }

    expected_date = extract_date_from_directory(directory_path.name)

    for file_path in directory_path.glob("*"):
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.mp4']:
            print(f"\\nFile: {file_path.name}")

            metadata = reader.read_dates(file_path)

            # Check what types of dates are available
            has_exif_original = metadata['exif_datetime_original'] is not None
            has_any_exif = any(metadata[k] for k in ['exif_datetime', 'exif_datetime_original', 'exif_datetime_digitized'])
            has_file_dates = any(metadata[k] for k in ['file_created', 'file_modified'])
            has_any_dates = any(metadata.values())

            # Update counters
            if has_exif_original:
                metadata_summary['files_with_exif_original'] += 1
            elif has_any_exif:
                metadata_summary['files_with_exif_any'] += 1
            elif has_file_dates:
                metadata_summary['files_with_file_dates_only'] += 1
            elif not has_any_dates:
                metadata_summary['files_with_no_dates'] += 1

            # Check for date mismatches
            best_date = reader.get_best_date(metadata)
            if best_date and abs((best_date.date() - expected_date).days) > 1:
                metadata_summary['date_mismatches'] += 1
                print(f"  DATE MISMATCH: {best_date.date()} vs expected {expected_date}")

            # Print metadata details
            for key, value in metadata.items():
                if value:
                    print(f"  {key}: {value}")

    print("\\n" + "=" * 40)
    print("SUMMARY:")
    for key, count in metadata_summary.items():
        print(f"  {key.replace('_', ' ').title()}: {count}")
    """


def example_5_command_line_usage():
    """Example 5: Using the command-line interface."""
    print("\n=== Example 5: Command Line Usage ===")

    print("The main script can be used from the command line:")
    print()
    print("# Basic usage - extract date from directory name")
    print('python main.py --directory "/path/to/2023.6.15 - Event"')
    print()
    print("# Specify date explicitly")
    print('python main.py --directory "/path/to/photos" --date "2023.6.15"')
    print()
    print("# Dry run to see what would be changed")
    print('python main.py --directory "/path/to/photos" --dry-run')
    print()
    print("# Verbose output for debugging")
    print('python main.py --directory "/path/to/photos" --verbose')
    print()
    print("# Full example with all options")
    print('python main.py --directory "/Users/shlomibenshushan/Library/CloudStorage/OneDrive-Personal/Photos/2023/2023.6.15 - Summer Party" --verbose --dry-run')


def example_6_platform_compatibility():
    """Example 6: Understanding platform compatibility."""
    print("\n=== Example 6: Platform Compatibility ===")

    writer = MetadataWriter()
    compatibility_info = writer.get_platform_compatibility_info()

    print("Platform Compatibility Information:")
    print("=" * 40)

    for platform, fields in compatibility_info.items():
        if platform != 'notes':
            print(f"\\n{platform.upper()}:")
            for field in fields:
                print(f"  - {field}")

    print("\\nIMPORTANT NOTES:")
    for key, note in compatibility_info['notes'].items():
        print(f"  {key}: {note}")

    print("\\nRECOMMENDATIONS:")
    print("  1. Always use EXIF DateTimeOriginal for photos when possible")
    print("  2. Keep file system timestamps as fallback")
    print("  3. Test with your specific devices and apps")
    print("  4. Create backups before making bulk changes")


def main():
    """Run all examples."""
    print("Photo Sorting Tool - Usage Examples")
    print("=" * 50)

    example_1_basic_usage()
    example_2_batch_processing()
    example_3_selective_updating()
    example_4_metadata_inspection()
    example_5_command_line_usage()
    example_6_platform_compatibility()

    print("\\n" + "=" * 50)
    print("For more information, see the README.md file.")


if __name__ == "__main__":
    main()