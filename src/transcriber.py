import logging
from pathlib import Path

import torch
import whisper

from .config import WhisperConfig
from .utils import estimate_ram_requirement, get_available_ram_gb, validate_audio_file

logger = logging.getLogger("podcast_ai_agent")


class TranscriptionError(Exception):
    """Base exception for transcription failures"""


class InsufficientMemoryError(TranscriptionError):
    """Raised when insufficient RAM for model"""


class InvalidAudioError(TranscriptionError):
    """Raised when audio file is invalid"""


class Transcriber:
    def __init__(self, config: WhisperConfig):
        self.config = config
        self.model = None

    def _load_model(self) -> whisper.Whisper:
        if self.model is not None:
            return self.model

        ram_required_gb = estimate_ram_requirement(self.config.model) / 1024
        ram_available_gb = get_available_ram_gb()

        if ram_available_gb < ram_required_gb:
            raise InsufficientMemoryError(
                f"Insufficient RAM: {ram_available_gb:.1f}GB available, "
                f"{ram_required_gb:.1f}GB required for {self.config.model} model"
            )

        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading {self.config.model} model on {device}...")

        try:
            self.model = whisper.load_model(self.config.model, device=device)
            return self.model
        except Exception as e:
            raise TranscriptionError(f"Failed to load model: {e}")

    def transcribe(self, audio_path: Path) -> dict:
        if not validate_audio_file(audio_path):
            raise InvalidAudioError(f"Invalid or corrupted audio: {audio_path}")

        model = self._load_model()

        logger.info(f"Transcribing {audio_path.name}...")
        kwargs = {
            "temperature": self.config.temperature,
        }

        if self.config.language != "auto":
            kwargs["language"] = self.config.language

        if self.config.translate:
            kwargs["task"] = "translate"

        try:
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                result = model.transcribe(str(audio_path), **kwargs)

                for warning in w:
                    if "FP16 is not supported on CPU" in str(warning.message):
                        logger.warning(f"Whisper Warning: {warning.message}")
                    else:
                        warnings.warn_explicit(
                            warning.message,
                            warning.category,
                            warning.filename,
                            warning.lineno,
                        )

            return result
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}")
