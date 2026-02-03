import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    rotation_size: int = 10 * 1024 * 1024,
) -> logging.Logger:
    logger = logging.getLogger("podcast_ai_agent")
    logger.setLevel(getattr(logging, level.upper()))

    class ColoredFormatter(logging.Formatter):
        GRAY = "\033[90m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        ORANGE = "\033[38;5;208m"
        RESET = "\033[0m"

        def format(self, record):
            timestamp_fmt = self.GRAY + "[%(asctime)s]" + self.RESET
            
            level_fmt = ""
            if record.levelno == logging.DEBUG:
                level_fmt = self.ORANGE + "%(levelname)-8s" + self.RESET
            elif record.levelno == logging.INFO:
                level_fmt = self.GREEN + "%(levelname)-8s" + self.RESET
            elif record.levelno == logging.WARNING:
                level_fmt = self.YELLOW + "%(levelname)-8s" + self.RESET
            elif record.levelno == logging.ERROR:
                level_fmt = self.RED + "%(levelname)-8s" + self.RESET
            elif record.levelno == logging.CRITICAL:
                level_fmt = self.RED + "%(levelname)-8s" + self.RESET
            else:
                level_fmt = "%(levelname)-8s"
                
            fmt = f"\n{timestamp_fmt} {level_fmt} %(message)s"
            formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S%z")
            return formatter.format(record)

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(ColoredFormatter())
    logger.addHandler(console)

    if log_file:
        file_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S%z"
        )
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(log_path, maxBytes=rotation_size, backupCount=3)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
