"""
Logging configuration for the photo sorting tool.

This module provides a comprehensive logging setup with colored output,
file logging, and appropriate log levels for different components.
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)  # Auto-reset colors after each print
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if COLORAMA_AVAILABLE:
            self.colors = {
                'DEBUG': Fore.CYAN,
                'INFO': Fore.GREEN,
                'WARNING': Fore.YELLOW,
                'ERROR': Fore.RED,
                'CRITICAL': Fore.RED + Back.WHITE + Style.BRIGHT
            }
        else:
            self.colors = {}

    def format(self, record):
        if COLORAMA_AVAILABLE and record.levelname in self.colors:
            # Add color to the level name
            colored_levelname = f"{self.colors[record.levelname]}{record.levelname}{Style.RESET_ALL}"

            # Create a copy of the record to avoid modifying the original
            record_copy = logging.makeLogRecord(record.__dict__)
            record_copy.levelname = colored_levelname

            return super().format(record_copy)

        return super().format(record)


def setup_logger(name: str = "photo_sorting",
                verbose: bool = False,
                log_file: Optional[str] = None,
                file_level: int = logging.DEBUG) -> logging.Logger:
    """
    Set up a comprehensive logger for the application.

    Args:
        name: Logger name
        verbose: Enable verbose (DEBUG) logging to console
        log_file: Path to log file (optional)
        file_level: Log level for file output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Set the base level
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_level = logging.DEBUG if verbose else logging.INFO
    console_handler.setLevel(console_level)

    # Console formatter with colors
    console_format = "%(asctime)s | %(levelname)-8s | %(message)s"
    console_formatter = ColoredFormatter(
        console_format,
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(file_level)

        # File formatter (no colors)
        file_format = "%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s"
        file_formatter = logging.Formatter(
            file_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logger.info(f"Logging to file: {log_path}")

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def create_session_log_file() -> str:
    """Create a log file path for the current session."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path.home() / ".photo_sorting" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return str(log_dir / f"photo_sorting_{timestamp}.log")


class LogContext:
    """Context manager for temporarily changing log level."""

    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.new_level = level
        self.old_level = None

    def __enter__(self):
        self.old_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)


def log_file_operation(logger: logging.Logger, operation: str, file_path: Path,
                      success: bool = True, details: str = None):
    """Log a file operation with consistent formatting."""
    status = "✓" if success else "✗"
    level = logging.INFO if success else logging.ERROR

    message = f"{status} {operation}: {file_path.name}"
    if details:
        message += f" ({details})"

    logger.log(level, message)


def log_metadata_change(logger: logging.Logger, file_path: Path,
                       field: str, old_value, new_value):
    """Log a metadata change with before/after values."""
    logger.info(f"Updated {file_path.name} | {field}: {old_value} -> {new_value}")


def log_processing_summary(logger: logging.Logger, total_files: int,
                          processed: int, modified: int, errors: int):
    """Log a processing summary with statistics."""
    logger.info("=" * 50)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total files found:   {total_files}")
    logger.info(f"Files processed:     {processed}")
    logger.info(f"Files modified:      {modified}")
    logger.info(f"Errors encountered:  {errors}")

    if total_files > 0:
        success_rate = (processed / total_files) * 100
        logger.info(f"Success rate:        {success_rate:.1f}%")

    logger.info("=" * 50)


# Pre-configured loggers for different modules
def get_date_parser_logger(verbose: bool = False) -> logging.Logger:
    """Get logger for date parsing operations."""
    return setup_logger("photo_sorting.date_parser", verbose=verbose)


def get_metadata_reader_logger(verbose: bool = False) -> logging.Logger:
    """Get logger for metadata reading operations."""
    return setup_logger("photo_sorting.metadata_reader", verbose=verbose)


def get_metadata_writer_logger(verbose: bool = False) -> logging.Logger:
    """Get logger for metadata writing operations."""
    return setup_logger("photo_sorting.metadata_writer", verbose=verbose)


# Example usage and testing
if __name__ == "__main__":
    # Test the logging setup
    logger = setup_logger(verbose=True, log_file=create_session_log_file())

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Test file operation logging
    test_path = Path("test_image.jpg")
    log_file_operation(logger, "Reading metadata", test_path, success=True,
                      details="Found EXIF data")
    log_file_operation(logger, "Writing metadata", test_path, success=False,
                      details="Permission denied")

    # Test metadata change logging
    log_metadata_change(logger, test_path, "DateTimeOriginal",
                       "2020:01:01 10:00:00", "2020:01:02 12:00:00")

    # Test summary logging
    log_processing_summary(logger, total_files=100, processed=95,
                          modified=45, errors=5)