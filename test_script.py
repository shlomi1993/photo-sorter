#!/usr/bin/env python3
"""
Test script for the photo sorting tool with sample data.

This script creates sample image files and tests the functionality.
"""

import os
import tempfile
from datetime import datetime, date
from pathlib import Path

from photo_sorting import extract_date_from_directory, MetadataReader, MetadataWriter, setup_logger


def create_sample_image(file_path: Path, width: int = 100, height: int = 100):
    """
    Create a simple test image file.
    """
    from PIL import Image

    # Create a simple test image
    img = Image.new('RGB', (width, height), color='red')
    img.save(file_path, 'JPEG')
    print(f"Created sample image: {file_path}")


def test_date_parsing():
    """
    Test the date parsing functionality.
    """
    print("\n=== Testing Date Parsing ===")

    test_cases = [
        "2020.1.2 - אחרי בוחן אמצע באינפי",
        "2022.12.25 - Christmas Party",
        "2023.5.10 - Family Vacation",
        "2021.3.14 - Pi Day Celebration",
        "invalid format",
        "2024.13.45 - Invalid Date"
    ]

    for test_dir in test_cases:
        result = extract_date_from_directory(test_dir)
        status = "✓" if result else "✗"
        print(f"{status} '{test_dir}' -> {result}")


def test_metadata_operations():
    """
    Test metadata reading and writing operations.
    """
    print("\n=== Testing Metadata Operations ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test directory structure
        event_dir = temp_path / "2023.6.15 - Test Event"
        event_dir.mkdir()

        # Create sample images
        image_files = [
            event_dir / "IMG_001.jpg",
            event_dir / "IMG_002.jpg",
            event_dir / "photo.jpeg"
        ]

        for img_file in image_files:
            create_sample_image(img_file)

        # Initialize components
        reader = MetadataReader()
        writer = MetadataWriter(dry_run=True)  # Use dry run for testing

        target_date = date(2023, 6, 15)

        print(f"\nProcessing files in: {event_dir}")
        print(f"Target date: {target_date}")

        for img_file in image_files:
            print(f"\n--- Processing {img_file.name} ---")

            # Read current metadata
            metadata = reader.read_dates(img_file)
            print("Current metadata:")
            for key, value in metadata.items():
                if value:
                    print(f"  {key}: {value}")
                else:
                    print(f"  {key}: Not set")

            # Test updating metadata (dry run)
            success = writer.update_dates(img_file, target_date)
            print(f"Update result: {'Success' if success else 'Failed'}")


def test_main_workflow():
    """
    Test the main workflow with a realistic scenario.
    """
    print("\n=== Testing Main Workflow ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a realistic directory structure
        event_dir = temp_path / "2023.8.20 - Summer Vacation"
        event_dir.mkdir()

        # Create various file types
        files_to_create = [
            "beach_photo1.jpg",
            "sunset.jpeg",
            "family_pic.jpg",
            "vacation_video.mp4",  # This will be empty but tests file detection
            "document.txt"  # This should be ignored
        ]

        for filename in files_to_create:
            file_path = event_dir / filename
            if filename.endswith(('.jpg', '.jpeg')):
                create_sample_image(file_path)
            else:
                # Create empty files for other types
                file_path.touch()

        # Extract date from directory name
        extracted_date = extract_date_from_directory(event_dir.name)
        print(f"Extracted date: {extracted_date}")

        # Find media files (same logic as main script)
        media_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp',
                          '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}

        media_files = []
        for ext in media_extensions:
            media_files.extend(event_dir.glob(f"*{ext}"))
            media_files.extend(event_dir.glob(f"*{ext.upper()}"))

        print(f"Found {len(media_files)} media files:")
        for media_file in media_files:
            print(f"  - {media_file.name}")

        # Test processing each file
        reader = MetadataReader()
        writer = MetadataWriter(dry_run=True)

        for media_file in media_files:
            print(f"\n--- Processing {media_file.name} ---")
            try:
                # Read metadata
                metadata = reader.read_dates(media_file)

                # Check if update is needed
                needs_update = False
                for date_type, current_date in metadata.items():
                    if current_date and current_date.date() != extracted_date:
                        print(f"  {date_type}: {current_date.date()} -> {extracted_date}")
                        needs_update = True
                    elif current_date:
                        print(f"  {date_type}: {current_date.date()} (OK)")
                    else:
                        print(f"  {date_type}: Not set -> {extracted_date}")
                        needs_update = True

                if needs_update:
                    success = writer.update_dates(media_file, extracted_date)
                    print(f"  Update: {'Success' if success else 'Failed'}")
                else:
                    print(f"  No changes needed")

            except Exception as e:
                print(f"  Error: {e}")


def main():
    """
    Run all tests.
    """
    print("Photo Sorting Tool - Test Script")
    print("=" * 40)

    # Setup logging
    logger = setup_logger(verbose=True)

    try:
        test_date_parsing()
        test_metadata_operations()
        test_main_workflow()

        print("\n" + "=" * 40)
        print("All tests completed!")
        print("\nNote: pyexiv2 is not available on this system, so EXIF")
        print("metadata reading/writing is limited. The tool will still")
        print("work with file system timestamps.")

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()