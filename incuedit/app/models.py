from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Literal

class Word(BaseModel):
    word_id: str
    text: str
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    speaker: str = "speaker_1"
    confidence: float = Field(default=1.0, ge=0, le=1)

class Transcript(BaseModel):
    words: list[Word]

class VideoCreate(BaseModel):
    filename: str
    duration_s: float = Field(gt=0)
    fps_num: int = Field(default=30, gt=0)
    fps_den: int = Field(default=1, gt=0)
    has_audio: bool = True
    source_sha256: str | None = None

class SessionCreate(BaseModel):
    video_id: str
    transcript: list[Word] = []

class InstructionRequest(BaseModel):
    say: str
    answer: str | None = None

class RestoreRequest(BaseModel):
    history_index: int | None = None
    label: str | None = None

class RenderRequest(BaseModel):
    callback_url: str | None = None

class JobResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    progress: int = 0
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

class ErrorEnvelope(BaseModel):
    error: dict[str, Any]
