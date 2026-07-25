"""
Photo Sorting Tool

A comprehensive tool for managing photo and video metadata to ensure
consistent date information across different platforms and applications.
"""

__version__ = "1.0.0"
__author__ = "Photo Sorting Tool"

from .date_parser import extract_date_from_directory, standardize_folder_name
from .metadata_reader import MetadataReader
from .metadata_writer import MetadataWriter
from .logger import setup_logger

__all__ = [
    "extract_date_from_directory",
    "standardize_folder_name",
    "MetadataReader",
    "MetadataWriter",
    "setup_logger"
]