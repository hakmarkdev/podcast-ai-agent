import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from typing_extensions import Annotated

from .config import Config, DownloadConfig, OutputConfig, WhisperConfig
from .downloader import DiskSpaceError, DownloadError, download_audio
from .logger import setup_logging
from .output import OutputWriter
from .transcriber import Transcriber, TranscriptionError
from .utils import check_ffmpeg, sanitize_filename

app = typer.Typer(
    name="podcast-ai-agent",
    help="Download and transcribe audio from YouTube videos.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print("Podcast AI Agent v0.1.0")
        raise typer.Exit()


@app.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", "-V", callback=version_callback, help="Show version and exit."
    ),
):
    pass


@app.command()
def process(
    url: Annotated[Optional[str], typer.Option("--url", "-u", help="YouTube video URL")] = None,
    batch_file: Annotated[
        Optional[Path],
        typer.Option("--batch-file", "-f", help="File containing URLs (one per line)", exists=True),
    ] = None,
    output_dir: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path(
        "./output"
    ),
    model: Annotated[
        str,
        typer.Option(
            "--model", "-m", help="Whisper model size (tiny, base, small, medium, large-v3)"
        ),
    ] = "base",
    language: Annotated[
        str, typer.Option("--language", "-l", help="Language code (auto for auto-detect)")
    ] = "auto",
    translate: Annotated[bool, typer.Option("--translate", help="Translate to English")] = False,
    format: Annotated[
        str, typer.Option("--format", help="Output format (txt, json, srt, vtt)")
    ] = "txt",
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose logging")
    ] = False,
    config_path: Annotated[
        Path, typer.Option("--config", "-c", help="Configuration file path", exists=True)
    ] = Path("config/default.yaml"),
    skip_download: Annotated[
        bool, typer.Option("--skip-download", help="Skip download if audio file exists")
    ] = False,
):
    if not check_ffmpeg():
        console.print("[red bold]Error:[/red bold] ffmpeg not found. Please install ffmpeg.")
        raise typer.Exit(code=1)

    try:
        config = Config.from_yaml(config_path)
    except Exception as e:
        console.print(f"[red]Error loading config:[/red] {e}")
        raise typer.Exit(code=1)

    if verbose:
        config.logging.level = "DEBUG"

    logger = setup_logging(
        level=config.logging.level,
        log_file=config.logging.file,
        rotation_size=(
            10 * 1024 * 1024
            if isinstance(config.logging.rotation, str)
            else config.logging.rotation
        ),
    )

    config.whisper.model = model
    config.whisper.language = language
    config.whisper.translate = translate
    config.output.directory = output_dir
    config.output.format = format

    urls = []
    if url:
        urls.append(url)
    elif batch_file:
        try:
            with open(batch_file) as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except Exception as e:
            console.print(f"[red]Error reading batch file:[/red] {e}")
            raise typer.Exit(code=1)
    else:
        console.print("[red]Error:[/red] You must provide either --url or --batch-file")
        raise typer.Exit(code=1)

    if not urls:
        console.print("[yellow]No URLs to process.[/yellow]")
        raise typer.Exit()

    success_count = 0
    fail_count = 0

    console.print(f"[bold]Processing {len(urls)} items...[/bold]")

    for i, current_url in enumerate(urls, 1):
        console.print(f"\n[bold cyan]Item {i}/{len(urls)}:[/bold cyan] {current_url}")

        try:
            if not skip_download:
                with console.status("Downloading...", spinner="dots"):
                    audio_path = download_audio(
                        current_url, config.output.directory, config.download
                    )
                console.print(f"[green]Downloaded:[/green] {audio_path.name}")
            else:
                with console.status("Checking/Downloading...", spinner="dots"):
                    audio_path = download_audio(
                        current_url, config.output.directory, config.download
                    )

            with console.status(f"Transcribing ({config.whisper.model})...", spinner="dots"):
                transcriber = Transcriber(config.whisper)
                result = transcriber.transcribe(audio_path)

            metadata = {
                "url": current_url,
                "model": config.whisper.model,
                "language": config.whisper.language,
                "translate": config.whisper.translate,
            }

            writer = OutputWriter(config.output.directory / audio_path.stem, metadata=metadata)
            if config.output.format == "txt":
                output_path = writer.write_txt(result["text"])
            elif config.output.format == "json":
                output_path = writer.write_json(result)
            elif config.output.format == "srt":
                output_path = writer.write_srt(result["segments"])
            elif config.output.format == "vtt":
                output_path = writer.write_vtt(result["segments"])
            else:
                raise ValueError(f"Unsupported format: {config.output.format}")

            console.print(
                f"[green bold]Success![/green bold] Saved to: [underline]{output_path}[/underline]"
            )
            logger.info(f"Successfully processed {current_url}")
            success_count += 1

        except DiskSpaceError as e:
            console.print(f"[red]Disk Space Error:[/red] {e}")
            logger.error(f"Disk space error for {current_url}: {e}")
            fail_count += 1
        except DownloadError as e:
            console.print(f"[red]Download Failed:[/red] {e}")
            logger.error(f"Download failed for {current_url}: {e}")
            fail_count += 1
        except TranscriptionError as e:
            console.print(f"[red]Transcription Failed:[/red] {e}")
            logger.error(f"Transcription failed for {current_url}: {e}")
            fail_count += 1
        except Exception as e:
            console.print(f"[red]Unexpected Error:[/red] {e}")
            logger.exception(f"Unexpected error for {current_url}")
            fail_count += 1

    if len(urls) > 1:
        console.print(f"\n[bold]Summary:[/bold] {success_count} succeeded, {fail_count} failed.")

    if fail_count > 0:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
