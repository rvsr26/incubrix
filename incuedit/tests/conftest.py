from __future__ import annotations
import json, subprocess
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app, VIDEOS, SESSIONS, JOBS, IDEMPOTENCY

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope="session")
def sample_video():
    p=ROOT/"examples"/"demo_media.mp4"
    if not p.exists():
        subprocess.run(["python",str(ROOT/"scripts"/"generate_demo_media.py")],check=True)
    return p

@pytest.fixture(scope="session")
def sample_words():
    return json.loads((ROOT/"examples"/"sample_transcript.json").read_text())

@pytest.fixture
def client():
    VIDEOS.clear(); SESSIONS.clear(); JOBS.clear(); IDEMPOTENCY.clear()
    with TestClient(app) as c:
        yield c
