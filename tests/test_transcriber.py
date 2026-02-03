from unittest.mock import MagicMock, patch

from src.config import WhisperConfig
from src.transcriber import Transcriber


def test_transcriber_init():
    config = WhisperConfig(model="base", language="en")
    transcriber = Transcriber(config)
    assert transcriber.config.model == "base"
    assert transcriber.config.language == "en"


@patch("src.transcriber.whisper.load_model")
@patch("src.transcriber.validate_audio_file")
def test_transcribe_success(mock_validate, mock_load_model, tmp_path):
    mock_validate.return_value = True

    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "Test transcription", "segments": []}
    mock_load_model.return_value = mock_model

    audio_path = tmp_path / "test.mp3"
    audio_path.touch()

    config = WhisperConfig()
    transcriber = Transcriber(config)
    result = transcriber.transcribe(audio_path)

    assert result["text"] == "Test transcription"
    mock_model.transcribe.assert_called_once()
