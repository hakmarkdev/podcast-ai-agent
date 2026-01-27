import json
from pathlib import Path
from typing import Any, Dict, List


def save_transcription(result: Dict[str, Any], path: Path, format: str) -> None:
    if format == "txt":
        path.write_text(result["text"], encoding="utf-8")
    elif format == "json":
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    elif format == "srt":
        write_srt(result["segments"], path)
    elif format == "vtt":
        write_vtt(result["segments"], path)
    else:
        raise ValueError(f"Unsupported format: {format}")


def write_srt(segments: List[Dict[str, Any]], path: Path) -> None:
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        text = seg["text"].strip().replace("\n", " ")
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_vtt(segments: List[Dict[str, Any]], path: Path) -> None:
    lines = ["WEBVTT\n"]
    for seg in segments:
        start = format_timestamp(seg["start"], vtt=True)
        end = format_timestamp(seg["end"], vtt=True)
        text = seg["text"].strip().replace("\n", " ")
        lines.append(f"\n{start} --> {end}\n{text}")

    path.write_text("\n".join(lines), encoding="utf-8")


def format_timestamp(seconds: float, vtt: bool = False) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    sep = "." if vtt else ","
    return f"{hours:02}:{minutes:02}:{secs:02}{sep}{millis:03}"
