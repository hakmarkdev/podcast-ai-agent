import pytest
from pathlib import Path
from unittest.mock import MagicMock
from src.config import Config

@pytest.fixture
def sample_config():
    return Config()

@pytest.fixture
def mock_ydl(mocker):
    mock = mocker.patch('yt_dlp.YoutubeDL')
    mock.return_value.__enter__.return_value.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 300,
        'ext': 'mp3'
    }

    mock.return_value.__enter__.return_value.download.return_value = None
    return mock

@pytest.fixture
def mock_whisper(mocker):
    mock = mocker.patch('whisper.load_model')
    mock.return_value.transcribe.return_value = {
        'text': 'Sample transcription.',
        'segments': [{'start': 0, 'end': 1, 'text': 'Sample'}],
    }
    return mock

@pytest.fixture
def sample_audio(tmp_path):
    from pydub import AudioSegment
    audio_path = tmp_path / "test.mp3"

    silent_audio = AudioSegment.silent(duration=1000)
    silent_audio.export(str(audio_path), format="mp3")
    return audio_path
