import logging
from logging.handlers import RotatingFileHandler

from .config import ERROR_LOG_FILE, LOG_FILE


LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def configure_logging(flask_app):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not _has_handler(root_logger, LOG_FILE):
        root_logger.addHandler(_build_file_handler(LOG_FILE, logging.INFO))

    if not _has_handler(root_logger, ERROR_LOG_FILE):
        root_logger.addHandler(_build_file_handler(ERROR_LOG_FILE, logging.ERROR))

    if not _has_console_handler(root_logger):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(console_handler)

    flask_app.logger.handlers = root_logger.handlers
    flask_app.logger.setLevel(logging.INFO)
    return root_logger


def _build_file_handler(path, level):
    handler = RotatingFileHandler(
        path,
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    return handler


def _has_handler(logger, path):
    return any(
        isinstance(handler, RotatingFileHandler)
        and getattr(handler, 'baseFilename', None) == path
        for handler in logger.handlers
    )


def _has_console_handler(logger):
    return any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
        for handler in logger.handlers
    )
