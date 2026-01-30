import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.downloader import download_audio
from src.config import DownloadConfig

def test_download_audio_success(tmp_path, mock_ydl):
    config = DownloadConfig()
    output_dir = tmp_path / "downloads"
    
    result = download_audio("http://test.com/video", output_dir, config)
    
    assert result == output_dir / "Test Video.mp3"
    assert (output_dir / "Test Video.mp3").parent.exists()

def test_download_audio_existing(tmp_path):
    config = DownloadConfig()
    output_dir = tmp_path / "downloads"
    output_dir.mkdir(parents=True)
    existing_file = output_dir / "Existing.mp3"
    existing_file.touch()

    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = {
            'title': 'Existing',
            'ext': 'mp3'
        }
        
        result = download_audio("http://test.com/video", output_dir, config)
        assert result == existing_file
