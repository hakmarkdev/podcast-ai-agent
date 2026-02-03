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


class YtDlpLogger:
    def debug(self, msg):
        if msg.startswith('[debug] '):
            logger.debug(msg)
        else:
            logger.debug(msg)

    def info(self, msg):
        if not msg.startswith('[download] '):
             logger.debug(msg)

    def warning(self, msg):
        logger.warning(msg)

    def error(self, msg):
        logger.error(msg)


def download_audio(
    url: str,
    output_dir: Path,
    config: DownloadConfig,
    progress_hook=None,
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
        "socket_timeout": config.socket_timeout,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "logger": YtDlpLogger(),
    }

    import shutil
    if shutil.which("deno"):
        pass
    elif shutil.which("node"):
        ydl_opts["js_runtimes"] = {"node": {}}
        ydl_opts["remote_components"] = {"ejs:github"}

    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]

    retry_count = 0
    backoff = config.retry_backoff

    while retry_count <= config.retries:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_id = info.get("id", "unknown_id")

                if video_id == "unknown_id":
                     title = info.get("title", "audio")
                     filename_base = sanitize_filename(title)
                else:
                     filename_base = sanitize_filename(video_id)

                output_path = output_dir / f"{filename_base}.{config.codec}"
                
                if output_path.exists():
                    logger.info(f"File already exists: {output_path}")
                    return output_path

                ydl_opts["outtmpl"] = str(output_dir / f"{filename_base}.%(ext)s")

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
