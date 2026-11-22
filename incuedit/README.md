# IncuEdit — Prompt-Based Video Editing Engine

**IncuBrix Software Engineer Assessment — Problem Statement 2 (PS2)**  
Candidate: **Rajala Vishnu Sathwick Reddy** (`rajalavishnureddy@gmail.com`)

IncuEdit is a prompt-based video editing engine that takes MP4/MOV media, word-aligned transcripts, and natural-language edit instructions, translates them into deterministic non-destructive timeline operations, and renders the result using FFmpeg.

---

## Key Highlights & Assessment Deliverables

- **Core Timeline Engine:** Fully non-destructive. Source video is immutable (SHA-256 verified before and after edits). Timeline segments map source intervals to current timeline time.
- **Content-Anchored Annotations:** Captions, mutes, bleeps, and speed warps anchor to transcript `word_id` values. Edits stick to content across cuts, reorders, speed adjustments, and restorations.
- **Strict 3-Way Answers:** Every editing command returns exactly one status: `applied`, `needs_clarification`, or `rejected`.
- **100% Deterministic Execution:** Identical sessions always produce the exact same timeline. Verified with 100% bitwise repeatability across 3 consecutive rounds of all 20 sessions (60 session runs; 0 mismatches).
- **Dual Studio Frontends:**
  - Modern React 18 + TypeScript + Vite Dark Studio mounted at [`/app`](http://localhost:8000/app).
  - Standalone Dark Studio with live player, interactive transcript, and visual timeline at [`/`](http://localhost:8000).
- **OpenTimelineIO (OTIO) Support:** Direct export via `GET /api/v1/sessions/{session_id}/otio` conforming to OTIO `Timeline.1` schema.
- **Comprehensive Test Suite:** **110 automated tests** passing in CI/Pytest with zero API keys required, including 42 scenario edge cases in `tests/test_scenarios_40.py`, security validation in `tests/test_security.py`, and diarization tests in `tests/test_speaker_diarization.py`.
- **Asynchronous FFmpeg Renderer:** Separate job pipeline with progress polling and optional HMAC-SHA256 signed callback webhooks (`X-IncuBrix-Signature`). Frame-accurate rendering verified with 0 frames A/V sync offset and 0 frames timeline length error on verified sample renders.
- **Production-Grade Security:** No hardcoded secrets. Environment-based webhook secret configuration with production startup enforcement and ephemeral random secret generation in development.
- **Honest Speaker Handling:** Explicit separation between transcription and speaker diarization. Transcriptions without diarization assign `unknown` labels. Destructive speaker cuts on unknown speakers trigger `needs_clarification`.

---

## Design Principles

1. **Source-Range Edit Decision List:** Segments record immutable source intervals (`source_start`, `source_end`) and playback speeds. Cuts, reorders, and keeps modify the interval mapping without altering the source file.
2. **Content-Anchored Annotations:** Captions and audio effects attach to stable transcript `word_id`s. Cutting an anchored range hides the effect; restoring that cut seamlessly restores the caption with exact original alignment.
3. **Current-Timeline Time Policy:** All numeric timestamps (e.g. "Cut from 0:10 to 0:20") reference the visible edited timeline (`current_timeline`). Semantic words map to original transcript word IDs.
4. **Deterministic Rule Engine Before LLM:** Editing operations are deterministic code. AI/LLM components are isolated to prompt understanding and never directly manipulate timeline state.

---

## API Overview & OpenAPI 3.1 Compliance

All business routes are under `/api/v1/`. Platform health and readiness probes are available at root and `/api/v1/`. Contract validation (`python scripts/validate_contract.py`) confirms a 100% match against `openapi.yaml` (23/23 routes).

| Method | Route | Description |
|---|---|---|
| GET | `/health`, `/ready` | Root platform liveness and readiness probes |
| GET | `/api/v1/health`, `/api/v1/ready` | Versioned service health checks |
| POST | `/api/v1/videos/upload` | Upload and probe MP4/MOV media (returns source SHA-256) |
| POST | `/api/v1/videos/from-url` | Secure HTTPS import of remote media |
| GET | `/api/v1/videos/{video_id}` | Retrieve video metadata and stream parameters |
| POST | `/api/v1/videos/{video_id}/transcribe` | Optional async transcription job |
| POST | `/api/v1/sessions` | Initialize editing session with word-level transcript |
| GET | `/api/v1/sessions/{session_id}` | Retrieve session status and active video ID |
| GET | `/api/v1/sessions/{session_id}/timeline` | Retrieve current timeline JSON and hash |
| GET | `/api/v1/sessions/{session_id}/transcript` | Retrieve word-aligned transcript |
| GET | `/api/v1/sessions/{session_id}/history` | Retrieve full edit history snapshots |
| POST | `/api/v1/sessions/{session_id}/instructions` | Apply natural-language edit instruction |
| POST | `/api/v1/sessions/{session_id}/music` | Upload background audio asset |
| POST | `/api/v1/sessions/{session_id}/undo` | Undo the last editing instruction |
| POST | `/api/v1/sessions/{session_id}/redo` | Redo the previously undone instruction |
| POST | `/api/v1/sessions/{session_id}/restore` | Restore a specific historic edit snapshot |
| GET | `/api/v1/sessions/{session_id}/otio` | Export timeline in OpenTimelineIO 1.0 JSON format |
| POST | `/api/v1/sessions/{session_id}/render` | Queue async video rendering job (returns 202 Accepted) |
| GET | `/api/v1/jobs/{job_id}` | Poll background job status and progress (0-100) |
| GET | `/api/v1/jobs/{job_id}/video` | Download rendered MP4 video |
| GET | `/api/v1/jobs/{job_id}/manifest` | Download cryptographic render manifest |

---

## Supported Natural-Language Operations

- **Cut & Remove:** `"Cut the first 30 seconds"`, `"Remove the last 10 seconds"`, `"Remove from 0:10 to 0:25"`, `"Cut the section from 1:00 to 1:30"`.
- **Keep:** `"Keep only the first 2 minutes"`, `"Keep from 0:30 to 1:30"`.
- **Speed Control:** `"Speed up from 0:00 to 0:10 by 2x"`, `"Slow down the first 5 seconds to 0.5x"`, `"Make this section faster/slower"` (enforces `0.25x` to `4.0x` boundaries).
- **Word-Level Mute & Bleep:** `"Mute the word confidential"`, `"Bleep the word secret"`, `"Bleep my phone number"`. Low-confidence words trigger confirmation rather than blind edits.
- **Captions & Overlays:** `"Add a caption saying Welcome"`, `"Add caption 'Hello World' from 0:02 to 0:06"`, `"Add captions to the complete video"`.
- **Caption Styling:** `"Make that caption red"`, `"Make that caption blue"`, `"Make that caption bigger"`, `"Make that caption smaller"`.
- **Speaker-Specific Cuts:** `"Remove what speaker 2 said"`, `"Cut speaker guest"`. If diarization was not run and speakers are `unknown`, returns `needs_clarification`.
- **Relative Cuts:** `"Remove everything after I say thanks"` (prompts for clarification when multiple occurrences exist).
- **Filler Word Removal:** `"Remove all filler words"` (cleans "um", "uh", and contextual "like").
- **Silence Removal:** `"Remove silences longer than 2 seconds"`.
- **Background Music & Ducking:** Upload music via API/studio and issue `"Add background music and lower it while I speak"`.
- **History & Undo/Redo:** `"Undo"`, `"Redo"`, `"Restore edit number 2"`, `"Put the intro back"`.
- **Clarification & Ambiguity:** Vague requests like `"Cut the boring part"` or `"Make it shorter"` return `needs_clarification` with specific actionable choices.

---

## Quick Start & Verification

### 1. Local Setup

```bash
cd incuedit

# Create and activate virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Install tested dependencies
pip install -r requirements-tested.txt
pip install openpyxl static-ffmpeg

# Copy environment config
copy .env.example .env

# Start FastAPI server
python -m uvicorn app.main:app --reload --port 8000
```

- Open the React Video Studio: <http://localhost:8000/app>
- Open the Standalone Dark Studio: <http://localhost:8000>
- Interactive OpenAPI Docs: <http://localhost:8000/docs>

### 2. Run Test Suite (110 Passing Pytest Tests)

```bash
python -m pytest -q
```
*Result:* **110 passed, 0 failed in ~16 seconds**.

### 3. Run Automated 20-Session Pack

```bash
python scripts/session_runner.py examples/sessions --output artifacts/session_pack
```

### 4. Verify 3-Round Determinism (60 Session Runs)

```bash
python scripts/verify_determinism.py
```
*Result:* **100% bitwise timeline determinism verified across all 3 rounds (20/20 sessions matching).**

### 5. Contract Validation

```bash
python scripts/validate_contract.py
```
*Result:* **Passed: True (23/23 routes match OpenAPI 3.1 specification).**

### 6. Clean Package & Extraction Verification

```bash
python scripts/package_and_verify.py
```
*Result:* Creates `IncuEdit_FINAL.zip`, extracts it to a clean temporary directory, executes all tests, builds the React frontend, validates contract, verifies determinism, and tests all API routes independently.

---

## Project Status Summary Table

| Requirement | Implementation | Evidence | Status |
|---|---|---|---|
| **Immutable Source** | Source SHA-256 verified before/after edits and render | `tests/test_api.py::test_upload_session_instruction_idempotency_and_render` | **Yes** |
| **Word-ID Anchors** | Captions/effects anchor to `word_id` across cuts/restores | `tests/test_timeline.py`, `tests/test_scenarios_40.py` | **Yes** |
| **Three-Way Answers** | Strictly `applied`, `needs_clarification`, or `rejected` | `artifacts/session_pack/results.json`, `app/engine.py` | **Yes** |
| **Timeline Determinism** | 20/20 sessions bitwise identical across 3 rounds (60 runs) | `artifacts/determinism_final/report.json` | **Yes** |
| **Render Accuracy** | 0 frames A/V offset and duration difference on verified renders | `artifacts/session_pack/*_manifest.json` | **Yes** |
| **Core Operations** | Cut, keep, reorder, speed (0.25-4x), mute, bleep, caption, ducking | `tests/test_timeline.py`, `tests/test_scenarios_40.py` | **Yes** |
| **Time Policy** | Explicit `current_timeline` policy declared and enforced | `app/parser.py`, `app/engine.py` | **Yes** |
| **OpenTimelineIO Export** | Standard OTIO 1.0 JSON export via `/api/v1/sessions/{id}/otio` | `app/timeline.py::export_otio`, scenario 33 | **Yes** |
| **Security & Webhooks** | Dynamic/configured `WEBHOOK_SECRET`, HMAC-SHA256, prod validation | `tests/test_security.py`, `app/config.py` | **Yes** |
| **Speaker Diarization** | Separate interface; `unknown` fallback; clarification on unknown speaker | `app/transcription.py`, `tests/test_speaker_diarization.py` | **Partial** (interface complete; external model omitted in default path) |
| **React Studio** | React 18.3.1 + TypeScript + Vite Dark Studio SPA | `frontend/src/`, `frontend/dist/` | **Yes** |
| **Docker Compose** | Config syntax validated (`docker compose config`) | `docker-compose.yml`, `Dockerfile`, `.dockerignore` | **Partial** (syntax valid; Docker daemon stopped on Windows host) |
| **60-Minute Scale** | Median 3.5ms on 16s short fixtures; 60m benchmark not run | `REPORT.md` Section 4 | **No** (honest: not benchmarked on 60m clip) |
