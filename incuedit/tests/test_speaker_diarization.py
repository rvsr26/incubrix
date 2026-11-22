"""Tests for speaker diarization, multi-speaker handling, and unknown speaker fallback."""
from __future__ import annotations
import pytest
from pathlib import Path
from app.transcription import (
    DiarizationUnavailable,
    DisabledDiarizationProvider,
    MockDiarizationProvider,
    PyannoteDiarizationProvider,
    get_diarization_provider,
)
from app.engine import EditingEngine
from app.timeline import new_timeline, duration

@pytest.fixture
def base_session():
    tl = new_timeline("test_video", 16.0, 30.0, True, "6ef412c82113941297a7cfb4394ccfb5cd931fa5dd6b067ad53a39debc10568d")
    return {
        "session_id": "test_spk_session",
        "video": {
            "video_id": "test_video",
            "duration_s": 16.0,
            "fps": 30.0,
            "has_audio": True,
            "source_sha256": "6ef412c82113941297a7cfb4394ccfb5cd931fa5dd6b067ad53a39debc10568d"
        },
        "timeline": tl,
        "transcript": [],
        "history": [],
        "pending": None,
        "warnings": []
    }

def test_diarization_provider_disabled_default():
    """Default provider marks unspecified speakers as unknown with clear warning."""
    words = [
        {"word_id": "w1", "text": "Hello", "start": 0.0, "end": 0.5},
        {"word_id": "w2", "text": "World", "start": 0.6, "end": 1.0, "speaker": "host"}
    ]
    provider = DisabledDiarizationProvider()
    updated, warnings = provider.diarize(Path("dummy.mp4"), words)
    assert updated[0]["speaker"] == "unknown"
    assert updated[1]["speaker"] == "host"
    assert any("Speaker diarization is disabled" in w for w in warnings)

def test_mock_diarization_provider_assigns_alternating_speakers():
    """Mock provider assigns speaker_1 / speaker_2 for testing multi-speaker flows."""
    words = [
        {"word_id": "w1", "text": "Hello", "start": 0.0, "end": 0.5},
        {"word_id": "w2", "text": "World", "start": 0.6, "end": 1.0}
    ]
    provider = MockDiarizationProvider()
    updated, warnings = provider.diarize(Path("dummy.mp4"), words)
    assert updated[0]["speaker"] == "speaker_1"
    assert updated[1]["speaker"] == "speaker_2"
    assert warnings == []

def test_pyannote_requires_hf_token(monkeypatch):
    """Pyannote provider fails safely when HF_TOKEN is missing."""
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("PYANNOTE_AUTH_TOKEN", raising=False)
    with pytest.raises(DiarizationUnavailable) as exc:
        PyannoteDiarizationProvider()
    assert "HF_TOKEN" in str(exc.value)

def test_speaker_cut_with_unknown_speakers_requests_clarification(base_session):
    """Destructive cut on unknown speaker triggers needs_clarification instead of failing blindly."""
    base_session["transcript"] = [
        {"word_id": "w1", "text": "This", "start": 0.5, "end": 1.0, "speaker": "unknown", "confidence": 0.99},
        {"word_id": "w2", "text": "video", "start": 1.1, "end": 1.5, "speaker": "unknown", "confidence": 0.99},
    ]
    engine = EditingEngine()
    r = engine.apply(base_session, "Remove what speaker 2 said")
    assert r["status"] == "needs_clarification"
    assert "unknown" in r["question"]
    assert len(r["options"]) >= 2

def test_speaker_cut_with_known_speakers_applies_cleanly(base_session):
    """When speaker IDs are known (e.g. manual transcript), cut removes only that speaker."""
    base_session["transcript"] = [
        {"word_id": "w1", "text": "Hello", "start": 0.5, "end": 1.0, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w2", "text": "There", "start": 1.2, "end": 2.0, "speaker": "speaker_2", "confidence": 0.99},
        {"word_id": "w3", "text": "Friend", "start": 2.2, "end": 3.0, "speaker": "speaker_1", "confidence": 0.99},
    ]
    engine = EditingEngine()
    r = engine.apply(base_session, "Remove what speaker 2 said")
    assert r["status"] == "applied"
    assert r["operations"][0]["type"] == "speaker_cut"
    assert duration(base_session["timeline"]) < 16.0

def test_overlapping_speech_detection():
    """Detect overlapping speech boundaries in word-aligned transcript."""
    words = [
        {"word_id": "w1", "text": "Hello", "start": 0.5, "end": 1.5, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w2", "text": "Hi", "start": 1.0, "end": 2.0, "speaker": "speaker_2", "confidence": 0.99},
    ]
    overlaps = []
    for i in range(len(words) - 1):
        if words[i]["end"] > words[i+1]["start"] and words[i]["speaker"] != words[i+1]["speaker"]:
            overlaps.append((words[i]["word_id"], words[i+1]["word_id"]))
    assert len(overlaps) == 1
    assert overlaps[0] == ("w1", "w2")

def test_low_confidence_word_flags_without_muting(base_session):
    """Low-confidence words flag a confirmation question rather than blindly muting."""
    base_session["transcript"] = [
        {"word_id": "w1", "text": "secret", "start": 1.0, "end": 1.5, "speaker": "speaker_1", "confidence": 0.45}
    ]
    engine = EditingEngine()
    r = engine.apply(base_session, "Mute the word secret")
    assert r["status"] == "needs_clarification"
    assert "low" in r["question"].lower() and "confidence" in r["question"].lower()
