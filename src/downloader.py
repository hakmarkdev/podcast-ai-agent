import logging
from pathlib import Path
from time import sleep

import yt_dlp

from .config import DownloadConfig
from .utils import check_disk_space, sanitize_filename

logger = logging.getLogger("podcast_ai_agent")


class DownloadError(Exception):
    """Base exception for download failures"""


class RateLimitError(DownloadError):
    """Raised when rate limited 429"""


class NetworkTimeoutError(DownloadError):
    """Raised when network times out"""


class DiskSpaceError(DownloadError):
    """Raised when insufficient disk space"""


def download_audio(
    url: str,
    output_dir: Path,
    config: DownloadConfig,
) -> Path:
    if not check_disk_space(output_dir, 0.1):
        raise DiskSpaceError(f"Insufficient disk space in {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        "format": config.format,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": config.codec,
            }
        ],
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "socket_timeout": config.socket_timeout,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    retry_count = 0
    backoff = config.retry_backoff

    while retry_count <= config.retries:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "audio")
                sanitized_title = sanitize_filename(title)
                output_path = output_dir / f"{sanitized_title}.{config.codec}"
                if output_path.exists():
                    logger.info(f"File already exists: {output_path}")
                    return output_path

                ydl_opts["outtmpl"] = str(output_dir / f"{sanitized_title}.%(ext)s")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl_final:
                    ydl_final.download([url])

                return output_path

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "too many requests" in error_msg:
                if retry_count < config.retries:
                    wait_time = backoff**retry_count
                    logger.warning(f"Rate limited. Waiting {wait_time:.1f}s...")
                    sleep(wait_time)
                    retry_count += 1
                    continue
                raise RateLimitError(f"Rate limit exceeded: {e}")
            raise DownloadError(f"Download failed: {e}")

        except Exception as e:
            if "timeout" in str(e).lower():
                raise NetworkTimeoutError(f"Network timeout: {e}")
            raise DownloadError(f"Unexpected error: {e}")

    raise DownloadError("Max retries exceeded")
