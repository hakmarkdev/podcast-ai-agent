from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from .constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_DOWNLOAD_CODEC,
    DEFAULT_DOWNLOAD_FORMAT,
    DEFAULT_LOG_FILE,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_ROTATION,
    DEFAULT_ON_EXISTING,
    DEFAULT_OUTPUT_DIRECTORY,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_RETRIES,
    DEFAULT_RETRY_BACKOFF,
    DEFAULT_SANITIZE_FILENAMES,
    DEFAULT_SOCKET_TIMEOUT,
    DEFAULT_WHISPER_LANGUAGE,
    DEFAULT_WHISPER_MODEL,
    DEFAULT_WHISPER_TEMPERATURE,
    DEFAULT_WHISPER_TRANSLATE,
)


class WhisperConfig(BaseModel):
    model: str = DEFAULT_WHISPER_MODEL
    language: str = DEFAULT_WHISPER_LANGUAGE
    translate: bool = DEFAULT_WHISPER_TRANSLATE
    temperature: float = DEFAULT_WHISPER_TEMPERATURE


class DownloadConfig(BaseModel):
    format: str = DEFAULT_DOWNLOAD_FORMAT
    codec: str = DEFAULT_DOWNLOAD_CODEC
    socket_timeout: int = DEFAULT_SOCKET_TIMEOUT
    retries: int = DEFAULT_RETRIES
    retry_backoff: float = DEFAULT_RETRY_BACKOFF


class OutputConfig(BaseModel):
    directory: Path = Field(default_factory=lambda: Path(DEFAULT_OUTPUT_DIRECTORY))
    format: Literal["txt", "srt", "json", "vtt"] = DEFAULT_OUTPUT_FORMAT
    sanitize_filenames: bool = DEFAULT_SANITIZE_FILENAMES
    on_existing: Literal["skip", "overwrite", "rename"] = DEFAULT_ON_EXISTING


class LoggingConfig(BaseModel):
    level: str = DEFAULT_LOG_LEVEL
    file: str | None = DEFAULT_LOG_FILE
    rotation: str = DEFAULT_LOG_ROTATION


class Config(BaseModel):
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    download: DownloadConfig = Field(default_factory=DownloadConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, path: Path | str = DEFAULT_CONFIG_PATH) -> "Config":
        path = Path(path)
        if not path.exists():
            return cls()

        with path.open() as f:
            data = yaml.safe_load(f) or {}

        return cls(
            whisper=WhisperConfig(**data.get("whisper", {})),
            download=DownloadConfig(**data.get("download", {})),
            output=OutputConfig(
                directory=Path(
                    data.get("output", {}).get("directory", str(DEFAULT_OUTPUT_DIRECTORY))
                ),
                **{k: v for k, v in data.get("output", {}).items() if k != "directory"},
            ),
            logging=LoggingConfig(**data.get("logging", {})),
        )
