from __future__ import annotations
import logging
import logging.handlers
import sys
from contextvars import ContextVar
from pathlib import Path

from novel_runtime.config import Settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

_OLD_FACTORY = logging.getLogRecordFactory()


def _record_factory(*args, **kwargs):
    record = _OLD_FACTORY(*args, **kwargs)
    record.request_id = get_request_id()
    return record


logging.setLogRecordFactory(_record_factory)


def get_request_id() -> str:
    return request_id_var.get()


def setup_logging(settings: Settings) -> None:
    logger = logging.getLogger("novel_runtime")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.handlers.clear()

    handlers: list[logging.Handler] = []

    console_handler = logging.StreamHandler(sys.stderr)
    if settings.log_format == "json":
        try:
            from pythonjsonlogger import jsonlogger
            formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                timestamp=True,
            )
        except ImportError:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s"
            )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s"
        )
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path), maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    for h in handlers:
        logger.addHandler(h)

    no_duplicate_propagation(logger)

    logger.info("logging_initialized", extra={
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "log_file": settings.log_file or "(stderr)",
    })


def no_duplicate_propagation(logger: logging.Logger) -> None:
    logger.propagate = False
