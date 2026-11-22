from __future__ import annotations
from pathlib import Path
import os
import logging

logger = logging.getLogger("incuedit.transcription")

class TranscriptionUnavailable(RuntimeError): pass
class DiarizationUnavailable(RuntimeError): pass

class TranscriptProvider:
    name = "abstract"
    def transcribe(self, path: Path) -> tuple[list[dict], list[str]]:
        """Returns (words, warnings)."""
        raise NotImplementedError

class ManualTranscriptProvider(TranscriptProvider):
    name = "manual"
    def transcribe(self, path: Path) -> tuple[list[dict], list[str]]:
        raise TranscriptionUnavailable("No automatic transcript provider is configured. Paste a word-level transcript or enable the optional faster-whisper provider.")

class FasterWhisperProvider(TranscriptProvider):
    name = "faster-whisper"
    def __init__(self):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriptionUnavailable("Install requirements-whisper.txt to enable the optional local transcription provider.") from exc
        model_name = os.getenv("WHISPER_MODEL", "base")
        self.model = WhisperModel(model_name, device=os.getenv("WHISPER_DEVICE", "cpu"), compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"))
        self.model_name = model_name

    def transcribe(self, path: Path) -> tuple[list[dict], list[str]]:
        segments, _info = self.model.transcribe(str(path), word_timestamps=True, vad_filter=True)
        words = []
        idx = 1
        for segment in segments:
            for w in segment.words or []:
                text = w.word.strip()
                if not text:
                    continue
                # Whisper does NOT perform speaker diarization; assign explicit 'unknown' label
                words.append({
                    "word_id": f"w{idx:06d}",
                    "text": text,
                    "start": max(0.0, float(w.start)),
                    "end": max(float(w.start) + 0.001, float(w.end)),
                    "speaker": "unknown",
                    "confidence": max(0.0, min(1.0, float(w.probability)))
                })
                idx += 1
        warnings = [
            "Speaker diarization was not performed; all recognized words have speaker assigned to 'unknown'."
        ]
        return words, warnings


class DiarizationProvider:
    name = "abstract"
    def diarize(self, path: Path, words: list[dict]) -> tuple[list[dict], list[str]]:
        """Returns (words_with_assigned_speakers, warnings)."""
        raise NotImplementedError

class DisabledDiarizationProvider(DiarizationProvider):
    name = "none"
    def diarize(self, path: Path, words: list[dict]) -> tuple[list[dict], list[str]]:
        # Preserve user-provided speaker labels if already present; otherwise set 'unknown'
        updated = []
        for w in words:
            w_copy = dict(w)
            if not w_copy.get("speaker") or w_copy.get("speaker") == "speaker_1":
                w_copy["speaker"] = "unknown"
            updated.append(w_copy)
        warnings = ["Speaker diarization is disabled in default path; speaker labels are marked as 'unknown'."]
        return updated, warnings

class MockDiarizationProvider(DiarizationProvider):
    name = "mock"
    def diarize(self, path: Path, words: list[dict]) -> tuple[list[dict], list[str]]:
        # For testing multi-speaker scenarios
        updated = []
        for i, w in enumerate(words):
            w_copy = dict(w)
            if not w_copy.get("speaker") or w_copy["speaker"] == "unknown":
                w_copy["speaker"] = "speaker_1" if i % 2 == 0 else "speaker_2"
            updated.append(w_copy)
        return updated, []

class PyannoteDiarizationProvider(DiarizationProvider):
    name = "pyannote"
    def __init__(self):
        auth_token = os.getenv("HF_TOKEN") or os.getenv("PYANNOTE_AUTH_TOKEN")
        if not auth_token:
            raise DiarizationUnavailable("pyannote.audio requires HF_TOKEN environment variable with accepted user terms on Hugging Face.")
        try:
            import pyannote.audio  # noqa: F401
        except ImportError as exc:
            raise DiarizationUnavailable("pyannote.audio is not installed. Install via pip install pyannote.audio") from exc

    def diarize(self, path: Path, words: list[dict]) -> tuple[list[dict], list[str]]:
        raise DiarizationUnavailable("Pyannote model weights require Hugging Face commercial licensing acceptance. Review pyannote license before commercial deployment.")


def get_transcription_provider() -> TranscriptProvider:
    selected = os.getenv("TRANSCRIPTION_PROVIDER", "manual").lower()
    if selected in {"manual", "mock", "none"}:
        return ManualTranscriptProvider()
    if selected in {"faster-whisper", "whisper"}:
        return FasterWhisperProvider()
    raise TranscriptionUnavailable(f"Unsupported TRANSCRIPTION_PROVIDER: {selected}")

def get_diarization_provider() -> DiarizationProvider:
    selected = os.getenv("DIARIZATION_PROVIDER", "none").lower()
    if selected in {"none", "disabled", "manual"}:
        return DisabledDiarizationProvider()
    if selected in {"mock", "test"}:
        return MockDiarizationProvider()
    if selected in {"pyannote"}:
        return PyannoteDiarizationProvider()
    raise DiarizationUnavailable(f"Unsupported DIARIZATION_PROVIDER: {selected}")

# Backward-compatible alias
def get_provider() -> TranscriptProvider:
    return get_transcription_provider()
