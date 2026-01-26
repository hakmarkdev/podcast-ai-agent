# Podcast AI Agent

Download and transcribe audio from YouTube videos using OpenAI's Whisper model.

## Prerequisites

- **Python 3.10+**
- **[uv](https://github.com/astral-sh/uv)** (Dependency manager)
- **[ffmpeg](https://ffmpeg.org/)** (Required for audio extraction)

## Installation

1. Clone the repository.
2. Install dependencies:

```bash
make install
```

## Usage

To run the agent:

```bash
make run
```

Or execute the CLI entry point directly via `uv`:

```bash
uv run podcast-ai-agent
```

## Configuration

Configuration is managed via `config/default.yaml` and environment variables. Key settings include:

- **Whisper**: Model size (`tiny`, `base`, `small`, `medium`, `large-v3`), language.
- **Download**: Audio format, codec, timeout.
- **Output**: Directory, file format (`txt`, `json`, `srt`, `vtt`).

## Development

We use `uv` for package management and `ruff`/`black` for linting/formatting.

Run all checks:

```bash
make check
```

Common commands:
- `make format`: Auto-format code.
- `make lint`: Check for linting errors.
- `make test`: Run unit tests.
- `make type-check`: Run static type analysis.
