import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class OutputWriter:
    def __init__(self, base_path: Path, metadata: Optional[Dict[str, Any]] = None):
        self.base_path = base_path
        self.metadata = metadata or {}

    def write_txt(self, text: str) -> Path:
        path = self._get_path("txt")
        path.write_text(text, encoding="utf-8")
        return path

    def write_json(self, result: Dict[str, Any]) -> Path:
        path = self._get_path("json")
        output = {
            "metadata": self.metadata,
            "transcription": result,
            "generated_at": datetime.utcnow().isoformat(),
        }
        path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def write_srt(self, segments: List[Dict[str, Any]]) -> Path:
        path = self._get_path("srt")
        lines = []
        for i, seg in enumerate(segments, 1):
            start = self._format_timestamp(seg["start"])
            end = self._format_timestamp(seg["end"])
            text = seg["text"].strip().replace("\n", " ")
            lines.append(f"{i}\n{start} --> {end}\n{text}\n")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def write_vtt(self, segments: List[Dict[str, Any]]) -> Path:
        path = self._get_path("vtt")
        lines = ["WEBVTT\n"]
        for seg in segments:
            start = self._format_timestamp(seg["start"], vtt=True)
            end = self._format_timestamp(seg["end"], vtt=True)
            text = seg["text"].strip().replace("\n", " ")
            lines.append(f"\n{start} --> {end}\n{text}")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _get_path(self, ext: str) -> Path:
        path = self.base_path.with_suffix(f".{ext}")

        if not path.exists():
            return path

        counter = 1
        while path.exists():
            path = self.base_path.with_name(f"{self.base_path.stem}_{counter}").with_suffix(
                f".{ext}"
            )
            counter += 1

        return path

    @staticmethod
    def _format_timestamp(seconds: float, vtt: bool = False) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        sep = "." if vtt else ","
        return f"{hours:02}:{minutes:02}:{secs:02}{sep}{millis:03}"
