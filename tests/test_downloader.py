from unittest.mock import patch


from src.config import DownloadConfig
from src.downloader import download_audio


def test_download_audio_success(tmp_path, mock_ydl):
    config = DownloadConfig()
    output_dir = tmp_path / "downloads"

    result = download_audio("http://test.com/video", output_dir, config)

    assert result == output_dir / "video_123.mp3"
    assert (output_dir / "video_123.mp3").parent.exists()


def test_download_audio_fallback(tmp_path):
    config = DownloadConfig()
    output_dir = tmp_path / "downloads"
    
    with patch("yt_dlp.YoutubeDL") as mock_ydl:
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = {
            "title": "Fallback Video",
            "ext": "mp3",
        }
        
        result = download_audio("http://test.com/video", output_dir, config)
        assert result == output_dir / "Fallback Video.mp3"


def test_download_audio_existing(tmp_path):
    config = DownloadConfig()
    output_dir = tmp_path / "downloads"
    output_dir.mkdir(parents=True)
    existing_file = output_dir / "video_existing.mp3"
    existing_file.touch()

    with patch("yt_dlp.YoutubeDL") as mock_ydl:
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = {
            "id": "video_existing",
            "title": "Existing",
            "ext": "mp3",
        }

        result = download_audio("http://test.com/video", output_dir, config)
        assert result == existing_file
