"""Console logging shared by execution and pipelines."""

import logging
import sys

logger = logging.getLogger("holodoppler")
logger.setLevel(logging.INFO)
logger.propagate = False


class _Formatter(logging.Formatter):
    def format(self, record):
        prefix = (
            f"{self.formatTime(record, '%Y-%m-%d %H:%M:%S')} "
            f"[{record.levelname.lower()}] [{record.name}] "
        )
        message = record.getMessage()
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        return "\n".join(prefix + line for line in message.splitlines())


def configure_logging() -> None:
    if not logger.handlers and sys.stderr is not None:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_Formatter())
        logger.addHandler(handler)


def get_logger(name):
    """Return a module logger using the shared application handlers."""
    return logging.getLogger(name)


configure_logging()
