import re
import shutil
from pathlib import Path

import psutil


def sanitize_filename(filename: str) -> str:
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, "_", filename)
    sanitized = sanitized.strip(". ")
    return sanitized[:200] if sanitized else "output"


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def get_available_ram_gb() -> float:
    return psutil.virtual_memory().available / (1024**3)


def validate_model_size(model: str) -> bool:
    valid_models = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
    return model in valid_models


def estimate_ram_requirement(model: str) -> int:
    requirements = {
        "tiny": 200,
        "base": 1000,
        "small": 2000,
        "medium": 5000,
        "large": 8000,
        "large-v2": 8000,
        "large-v3": 8000,
    }
    return requirements.get(model, 1000)


def validate_audio_file(path: Path) -> bool:
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(path)
        return len(audio) > 0
    except Exception:
        return False
