"""
Date parsing utilities for extracting dates from directory names.

This module handles parsing dates from directory names that follow the format: YYYY.MM.DD - Event Name

The event name can contain Unicode characters including Hebrew text.
"""

import re
import logging

from datetime import datetime, date
from typing import Optional


logger = logging.getLogger(__name__)


def extract_date_from_directory(directory_name: str) -> Optional[date]:
    """
    Extract date from directory name following the format: YYYY.MM.DD - Event Name

    Args:
        directory_name (str): Name of the directory (e.g., "2020.1.2 - אחרי בוחן ").

    Returns:
        Optional[date]: The extracted date, or None if parsing fails.
    """
    # Pattern to match YYYY.MM.DD or YYYY.M.D at the start of the string
    # Allows for single or double digit months and days
    pattern = r'^(\d{4})\.(\d{1,2})\.(\d{1,2})\s*-'

    match = re.match(pattern, directory_name.strip())

    if not match:
        logger.warning(f"Could not extract date from directory name: '{directory_name}'")
        return None

    try:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        # Validate the date
        parsed_date = date(year, month, day)

        logger.debug(f"Extracted date {parsed_date} from directory name: '{directory_name}'")
        return parsed_date

    except ValueError as e:
        logger.error(f"Invalid date components in directory name '{directory_name}': {e}")
        return None


def parse_date_string(date_str: str, formats: list = None) -> Optional[datetime]:
    """
    Parse a date string using multiple possible formats.

    Args:
        date_str (str): Date string to parse.
        formats (Optional[list[str]]): Date formats to try, or None to use the defaults.

    Returns:
        Optional[datetime]: The parsed datetime, or None if all formats fail.
    """
    if formats is None:
        formats = [
            "%Y.%m.%d",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d.%m.%Y",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y.%m.%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
        ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse date string: '{date_str}'")
    return None


def validate_date_range(date_obj: date, min_year: int = 1980, max_year: int = None) -> bool:
    """
    Validate that a date falls within a reasonable range for photos.

    Args:
        date_obj (date): Date to validate.
        min_year (int): Minimum acceptable year.
        max_year (Optional[int]): Maximum acceptable year, or None to use the
            current year plus one.

    Returns:
        bool: True if the date is in the valid range, otherwise False.
    """
    if max_year is None:
        max_year = datetime.now().year + 1

    if date_obj.year < min_year or date_obj.year > max_year:
        logger.warning(f"Date {date_obj} is outside reasonable range ({min_year}-{max_year})")
        return False

    return True


def standardize_folder_name(directory_name: str) -> Optional[str]:
    """
    Standardize folder name to YYYY.MM.DD format by adding leading zeros where needed.

    Converts formats like:
    - YYYY.M.D -> YYYY.MM.DD
    - YYYY.MM.D -> YYYY.MM.DD
    - YYYY.M.DD -> YYYY.MM.DD

    Args:
        directory_name (str): Directory name that may need standardization.

    Returns:
        Optional[str]: The standardized name, or None if no changes are needed.

    Examples:
        >>> standardize_folder_name("2020.1.2 - Birthday Party")
        '2020.01.02 - Birthday Party'

        >>> standardize_folder_name("2020.12.5 - Christmas")
        '2020.12.05 - Christmas'

        >>> standardize_folder_name("2020.01.02 - Already Standard")
        None
    """
    # Pattern to match YYYY.M.D or YYYY.MM.D or YYYY.M.DD formats
    pattern = r'^(\d{4})\.(\d{1,2})\.(\d{1,2})(\s*-\s*.+)?$'
    match = re.match(pattern, directory_name.strip())

    if not match:
        return None

    year = match.group(1)
    month = match.group(2)
    day = match.group(3)
    suffix = match.group(4) or ""  # Event name part (including " - ")

    # Check if standardization is needed (month or day needs leading zero)
    month_padded = month.zfill(2)
    day_padded = day.zfill(2)

    # If already standardized, return None
    if month == month_padded and day == day_padded:
        return None

    # Create standardized name
    standardized_name = f"{year}.{month_padded}.{day_padded}{suffix}"

    logger.info(f"Folder name standardization: '{directory_name}' -> '{standardized_name}'")
    return standardized_name


def get_event_name_from_directory(directory_name: str) -> Optional[str]:
    """
    Extract the event name portion from a directory name.

    Args:
        directory_name (str): Full directory name.

    Returns:
        Optional[str]: The event name, or None if the directory does not match the expected format.
    """
    pattern = r'^\d{4}\.\d{1,2}\.\d{1,2}\s*-\s*(.+)$'
    match = re.match(pattern, directory_name.strip())

    if match:
        event_name = match.group(1).strip()
        logger.debug(f"Extracted event name: '{event_name}' from directory: '{directory_name}'")
        return event_name

    logger.warning(f"Could not extract event name from directory: '{directory_name}'")
    return None
