import inspect

from pydantic import BaseModel


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "paideia"
    LOG_FORMAT: str = "{log_color}{levelname:<8s}:{asctime}:{name:>8s}::{message}"
    LOG_STYLE: str = "{"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    version = 1
    disable_existing_loggers = False
    formatters = {
        "default": {
            "()": "colorlog.ColoredFormatter",
            "format": LOG_FORMAT,
            "style": LOG_STYLE,
            # 'datefmt': '%m-%d %H:%M:%S',
        },
    }
    handlers = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers = {
        "paideia": {"handlers": ["default"], "level": LOG_LEVEL},
    }


def myself():
    return inspect.stack()[1][3]
