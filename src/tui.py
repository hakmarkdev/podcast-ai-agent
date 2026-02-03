from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Log, Input, Button, Label, ProgressBar
from textual import work
from textual.worker import Worker

import logging
from .tui_logger import setup_tui_logging
from .config import DownloadConfig, WhisperConfig
from .downloader import download_audio
from .transcriber import Transcriber

# Import global logger to ensure it's the same instance
logger = logging.getLogger("podcast_ai_agent")

class PodcastAgentApp(App):
    """A Textual app for Podcast AI Agent."""

    CSS = """
    Screen {
        layout: vertical;
    }
    
    #input-container {
        height: auto;
        dock: top;
        padding: 1;
        border-bottom: solid green;
    }
    
    #url-input {
        width: 100%;
    }
    
    #action-buttons {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }
    
    Button {
        margin-right: 1;
    }
    
    #log-container {
        height: 1fr;
        border: solid blue;
    }
    
    Log {
        height: 100%;
    }
    
    #status-bar {
        height: auto;
        dock: bottom;
        padding: 1;
        background: $boost;
    }
    
    ProgressBar {
        width: 100%;
        margin-bottom: 1;
        display: none;
    }
    """

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        
        with Container(id="input-container"):
            yield Label("YouTube URL:")
            yield Input(placeholder="Enter YouTube URL here...", id="url-input")
            with Container(id="action-buttons"):
                yield Button("Download & Transcribe", id="btn-process", variant="primary")
                yield Button("Download Only", id="btn-download")
                yield Button("Transcribe Only", id="btn-transcribe")

        with Container(id="log-container"):
            yield Log(id="log-output", markup=True)

        with Container(id="status-bar"):
            yield Label("Ready", id="status-label")
            yield ProgressBar(id="progress-bar", total=100, show_eta=True)

        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        log_widget = self.query_one("#log-output", Log)
        setup_tui_logging(log_widget, level="INFO")
        logger.info("Application started. Ready to process.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        url_input = self.query_one("#url-input", Input)
        url = url_input.value.strip()

        if not url:
            logger.warning("Please enter a valid URL.")
            return

        if event.button.id == "btn-process":
            self.action_process(url, transcribe=True)
        elif event.button.id == "btn-download":
            self.action_process(url, transcribe=False)
        # Transcribe only logic would likely need a file selector, skipping for now based on current input

    def action_process(self, url: str, transcribe: bool = True) -> None:
        """Start the processing workflow."""
        self.query_one("#btn-process", Button).disabled = True
        self.query_one("#btn-download", Button).disabled = True
        
        # Reset progress
        pbar = self.query_one("#progress-bar", ProgressBar)
        pbar.display = True
        pbar.update(total=100, progress=0)
        
        self.run_process_worker(url, transcribe)

    @work(thread=True)
    def run_process_worker(self, url: str, transcribe: bool) -> None:
        """Run the heavy lifting in a worker thread."""
        try:
            # 1. Download
            self.post_message_status(f"Downloading {url}...")
            
            # Configs
            dl_config = DownloadConfig() # Defaults
            # You might want to allow configuring output dir via UI later
            output_dir = Path("output/downloads")
            
            # --- DOWNLOAD ---
            logger.info(f"Starting download: {url}")
            
            def download_progress_hook(d):
                """Hook for yt-dlp to update Textual progress bar."""
                if d['status'] == 'downloading':
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    if total_bytes:
                        percentage = (downloaded_bytes / total_bytes) * 100
                        # Update progress bar (Download takes 0-50% of total visual progress if transcribing, else 0-100%)
                        # Let's simplify and just show download progress 0-100% then reset for transcribe?
                        # Or split: Download 50%, Transcribe 50%
                        
                        visual_progress = percentage
                        if transcribe:
                            visual_progress = visual_progress / 2
                            
                        self.post_message_progress(visual_progress, 100)

            # We need to pass a callback that `downloader.py` can use.
            # `downloader.py` expects a hook that receives the `d` dict from yt-dlp.
            # We'll pass `download_progress_hook` directly.
            
            from .downloader import download_audio
            audio_path = download_audio(url, output_dir, dl_config, progress_hook=download_progress_hook)
            
            logger.info(f"Download complete: {audio_path}")
            
            if not transcribe:
                self.post_message_status("Finished!")
                self.post_message_completed()
                return


            # --- TRANSCRIBE ---
            self.post_message_status(f"Transcribing {audio_path.name}...")
            logger.info("Starting transcription...")
            
            whisper_config = WhisperConfig() # Defaults
            transcriber = Transcriber(whisper_config)
            
            # Transcription now doesn't support progress callback
            result = transcriber.transcribe(audio_path)
            
            # Save transcript
            transcript_path = audio_path.with_suffix(".txt")
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(result["text"])
                
            logger.info(f"Transcription complete: {transcript_path}")
            self.post_message_status("Finished!")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            self.post_message_status(f"Error: {e}")
        finally:
            self.post_message_completed()

    # --- Helpers to update UI from worker ---
    
    def post_message_status(self, message: str) -> None:
        """Update status label safely."""
        self.call_from_thread(self.update_status, message)
        
    def update_status(self, message: str) -> None:
        self.query_one("#status-label", Label).update(message)

    def post_message_progress(self, current: float, total: float) -> None:
        """Update progress bar safely."""
        self.call_from_thread(self.update_progress, current, total)
        
    def update_progress(self, current: float, total: float) -> None:
        pbar = self.query_one("#progress-bar", ProgressBar)
        pbar.update(total=total, progress=current)

    def post_message_completed(self) -> None:
        """Reset UI state safely."""
        self.call_from_thread(self.reset_ui)
        
    def reset_ui(self) -> None:
        self.query_one("#btn-process", Button).disabled = False
        self.query_one("#btn-download", Button).disabled = False
        self.query_one("#btn-transcribe", Button).disabled = False
        # Keep progress bar visible at 100% or hide it? 
        # pbar = self.query_one("#progress-bar", ProgressBar)
        # pbar.display = False


if __name__ == "__main__":
    app = PodcastAgentApp()
    app.run()
