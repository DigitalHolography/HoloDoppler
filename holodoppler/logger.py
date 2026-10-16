"""Console logging shared by execution and pipelines."""

import logging
import sys
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pprint import pformat

logger = logging.getLogger("holodoppler")
logger.setLevel(logging.INFO)
logger.propagate = False


class _Formatter(logging.Formatter):
    def format(self, record):
        prefix = f"{self.formatTime(record, '%H:%M:%S')} [{record.levelname.lower()}] "
        message = record.getMessage()
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        return "\n".join(prefix + line for line in message.splitlines())


def configure_logging() -> None:
    if not logger.handlers and sys.stderr is not None:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_Formatter())
        logger.addHandler(handler)


def log_mapping(label, values, *, level=logging.INFO) -> None:
    """Render dictionaries and metadata dataclasses without copying their data."""
    lines = [f"{label}:"]

    def as_mapping(value):
        if is_dataclass(value) and not isinstance(value, type):
            return {field.name: getattr(value, field.name) for field in fields(value)}
        return value

    def append(mapping, indent):
        for key, value in mapping.items():
            value = as_mapping(value)
            if isinstance(value, Mapping):
                lines.append(f"{' ' * indent}{key}:")
                append(value, indent + 2)
            else:
                rendered = pformat(value, sort_dicts=False).splitlines()
                lines.append(f"{' ' * indent}{key}: {rendered[0]}")
                lines.extend(' ' * (indent + 2) + line for line in rendered[1:])

    values = as_mapping(values)
    if isinstance(values, Mapping):
        append(values, 2)
    else:
        lines.extend("  " + line for line in pformat(values, sort_dicts=False).splitlines())
    logger.log(level, "\n".join(lines))


configure_logging()
