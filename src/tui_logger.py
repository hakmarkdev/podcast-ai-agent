import logging
from rich.text import Text
from textual.widgets import Log


class TextualLogHandler(logging.Handler):
    """
    A logging handler that writes to a Textual Log widget.
    """

    def __init__(self, log_widget: Log):
        super().__init__()
        self.log_widget = log_widget
        self.formatter = logging.Formatter("%(message)s")  # Simple format, rich will handle styling

    def emit(self, record):
        try:
            msg = self.format(record)
            
            # Map log levels to Rich colors/styles
            style = ""
            if record.levelno == logging.DEBUG:
                style = "dim"
            elif record.levelno == logging.INFO:
                style = "green"
            elif record.levelno == logging.WARNING:
                style = "yellow"
            elif record.levelno == logging.ERROR:
                style = "red"
            elif record.levelno == logging.CRITICAL:
                style = "bold red"

            # Create a localized timestamp
            import datetime
            timestamp = datetime.datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            
            # Construct the log message
            log_text = Text()
            log_text.append(f"[{timestamp}] ", style="dim")
            log_text.append(f"{record.levelname:<8}", style=style)
            log_text.append(msg)

            # Write safely to the Log widget (must be thread-safe if called from worker)
            # Textual widgets are generally thread-safe for simple writes, 
            # but if we are in a different thread, we should use call_from_thread or post_message.
            # However, `Log.write` schedules the write on the main thread automatically in recent Textual versions.
            # To be safe and compliant with best practices:
            self.log_widget.write(log_text)
            
        except Exception:
            self.handleError(record)


def setup_tui_logging(log_widget: Log, level: str = "INFO") -> logging.Logger:
    """
    Sets up the logger to output to the provided Textual Log widget.
    """
    logger = logging.getLogger("podcast_ai_agent")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplicates/conflicts
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    handler = TextualLogHandler(log_widget)
    logger.addHandler(handler)
    
    return logger
