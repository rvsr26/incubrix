# IncuEdit (PS2) — Comprehensive Project Audit

**Project:** IncuEdit — Prompt-Based Video Editing Engine (IncuBrix Assessment 2 / PS2)  
**Candidate:** Rajala Vishnu Sathwick Reddy  
**Date:** November 18, 2026  
**Auditor Role:** Senior Software Architect, Full-Stack Engineer, QA & DevOps Engineer  

---

## 1. Executive Summary

This audit evaluates the codebase in `IncuEdit_PS2_Complete_Project/incuedit` against all requirements of the IncuBrix Problem Statement 2 (PS2) brief and Master Build specification.

The project already possesses a solid core architectural foundation:
- An **immutable source-media model** where edits are non-destructive timeline decision slices (`source_start`, `source_end`, `speed`).
- **Word-ID anchored annotations**: Captions, mute, and bleep effects anchor to transcript word IDs, surviving cuts, reordering, speed variations, and snapshot restoration.
- **Strict 3-way response format**: `applied`, `needs_clarification`, and `rejected`.
- **Separate asynchronous FFmpeg renderer**: Renders the timeline into playable MP4, ducks background music under speech using sidechain compression, and enforces duration and A/V sync within 1 frame.
- **FastAPI service** with OpenAPI 3.1 schema, `Idempotency-Key` headers, structured JSON logging, correlation IDs, and background jobs.
- **Batch session runner** capable of playing automated YAML/JSON test sessions.

However, several critical gaps, unverified claims, and incomplete components exist that prevent this from being a top-tier production-grade submission:
1. **Frontend Interface**: Currently a single raw HTML/JS file (`web/index.html`) rather than a modern React + TypeScript + Vite + Tailwind CSS editing studio.
2. **OpenTimelineIO (OTIO) Export**: Not yet implemented.
3. **Automated Test Scenarios**: Currently 56 test cases covering 20 sessions; the specification requires at least 40 dedicated scripted test scenarios for CI covering all edge cases (hard cases, speaker swaps, overlapping speech, VFR, caption color styling, multi-part requests, etc.).
4. **Natural Language Parser Extensibility**: Missing support for caption styling (e.g. "make that caption red"), speaker-based editing, multi-part operations with atomicity/rollback, and rich clarification handling.
5. **Job Callback Webhook**: IncuBrix integration standard requires an optional webhook callback signed with HMAC-SHA256 in an `X-IncuBrix-Signature` header.
6. **Persistence & Durability**: State is held in volatile in-memory dicts, vulnerable to process crashes.
7. **Assessment Workbook**: `Assessment2_Rajala_Vishnu_Sathwick_Reddy.xlsx` contains placeholder entries and needs complete synchronization with real test evidence.

---

## 2. Component-by-Component Audit

### 2.1 Core Timeline Engine (`app/timeline.py`)
- **Status:** **WORKING & HIGH QUALITY**
- **Strengths:**
  - Non-destructive edit decision list with immutable source video (`source_sha256` verified).
  - Explicit `current_timeline` time policy.
  - Slicing logic correctly translates current visible clock intervals into underlying source clips.
  - Word anchors (`word_positions`) correctly calculate output timings based on the current segment progression and segment playback rates.
  - Timeline hashing is deterministic across process restarts.
- **Gaps to Address:**
  - OpenTimelineIO export helper is missing.
  - Caption styling attributes should support color customization (e.g. "red", "yellow").

### 2.2 Instruction Parser & Engine (`app/parser.py`, `app/engine.py`)
- **Status:** **WORKING FOR CORE; EXPANSION NEEDED FOR HARD CASES**
- **Strengths:**
  - Deterministic regex parser maps phrases to typed operations without direct LLM mutation of state.
  - Semantic synonym mapping (`pricing` -> `cost`, `budget`, etc.).
  - Clarification loop stores pending state and resolves with "first", "second", or "all".
  - Low-confidence word bleep confirmation prevents accidental censorship.
  - Duplicate destructive edit detection prevents accidental double-cuts.
- **Gaps to Address:**
  - Caption styling: "Make that caption red" / "Change caption color to yellow".
  - Speaker-specific editing: "Remove everything speaker 2 said".
  - Multi-part requests with atomic rollback: "Cut 0:00 to 0:05 and add caption 'Hello'".
  - Compound / relative cuts: "Remove everything after I say thanks".
  - "Make it bigger" when no caption exists should cleanly return `CAPTION_NOT_FOUND` (already handled, verify in test).
  - 10x speed requests should cleanly reject with `UNSUPPORTED_SPEED` (limit is 0.25x - 4.0x).

### 2.3 Video Rendering Engine (`app/render.py`)
- **Status:** **WORKING WITH FFMPEG 8.0/7.1**
- **Strengths:**
  - Asynchronous background execution.
  - Complex FFmpeg filter graph: `trim`, `setpts`, `atrim`, `asetpts`, `atempo`, `concat`, `drawtext`, `sidechaincompress`, `apad`.
  - Sidechain ducking of background music under original audio.
  - Programmatic verification of output file via `ffprobe` checking video and audio duration within 1 frame tolerance.
- **Improvements:**
  - Ensure fallback detection of FFmpeg/FFprobe binaries across OS environments (Windows, Linux, macOS).
  - Clean temporary files on render failure.

### 2.4 API & Integration Standards (`app/main.py`)
- **Status:** **MOSTLY COMPLETE; MINOR ADDITIONS REQUIRED**
- **Strengths:**
  - All routes scoped under `/api/v1/`.
  - `Idempotency-Key` header enforced on all POST endpoints with SHA-256 request payload caching.
  - Structured JSON logging with `timestamp`, `level`, `job_id`, `correlation_id`, `method`, `path`, `status_code`, `latency_ms`.
  - `/health` and `/ready` endpoints.
  - Standard error envelope: `{"error": {"code", "message", "retryable", "details"}}`.
- **Gaps to Address:**
  - Background job webhook callback: support optional `callback_url` with HMAC-SHA256 signature in `X-IncuBrix-Signature`.
  - OTIO export endpoint: `GET /api/v1/sessions/{session_id}/otio`.

### 2.5 Frontend Studio (`web/`)
- **Status:** **PARTIAL (LEGACY HTML/JS)**
- **Audit:**
  - Currently `web/index.html` is a single vanilla HTML file.
  - The assessment specification requires a modern, responsive React + TypeScript + Vite + Tailwind CSS editing studio with:
    - Landing and upload panel with progress.
    - Video preview player with timeline synchronization.
    - Interactive transcript viewer with timestamps, speaker labels, and confidence tags.
    - Prompt command bar with quick suggestions.
    - 3-way response display (Applied / Needs Clarification / Rejected).
    - Interactive visual timeline track showing cut segments, speed multipliers, and caption/effect markers.
    - Undo / Redo and Edit History snapshot inspector.
    - Render queue trigger and output MP4 download.
- **Action:** Build a production React + TypeScript + Vite + Tailwind frontend and embed its built distribution into the FastAPI service.

### 2.6 Test Suite & Verification (`tests/`, `scripts/`)
- **Status:** **56 PASSING TESTS; NEED 40+ SCRIPTED CI SCENARIOS**
- **Audit:**
  - Existing suite has 56 tests (`test_timeline.py`, `test_api.py`, `test_session_runner.py`).
  - Need dedicated 40+ scenario test matrix covering all hard cases from Page 4 of the Brief:
    1. Caption followed by cut
    2. Restore cut and caption recovery
    3. Reorder then mute
    4. Filler removal intersecting a bleep
    5. Duplicate cuts prevention
    6. Invalid timestamp out of range
    7. Short video with out-of-range caption
    8. Multiple pricing mentions clarification
    9. "The second one" answer
    10. "All of them" answer
    11. Undo and redo sequence
    12. Restore specific earlier edit
    13. Restore intro while preserving unrelated edits
    14. Speed changes (2x)
    15. Slow down (0.5x)
    16. Overlapping speed changes
    17. Ten-times speed rejection
    18. Cut everything rejection
    19. Caption with partially removed words
    20. Sped-up caption minimum readable duration (0.7s)
    21. Missing caption target error
    22. Repeated instructions idempotency
    23. Deliberate pauses preservation
    24. Low-confidence transcript words confirmation
    25. Speaker-specific removal
    26. Two-speaker overlap warning
    27. Speaker-label inconsistency warning
    28. Video with no audio handling
    29. Variable-frame-rate warning/probe
    30. Background music upload and ducking
    31. Three-part request with one impossible operation (atomic failure)
    32. Partial failure prevention
    33. Idempotent job requests
    34. Job status progression (queued -> running -> succeeded)
    35. Render duration verification within 1 frame
    36. Render A/V offset verification within 1 frame
    37. Original media hash preservation
    38. Batch runner execution on folder
    39. API structured error envelope validation
    40. OpenTimelineIO export validation
    41. Determinism validation (3 consecutive runs)

---

## 3. Dependencies and Licensing Review

| Dependency | Version Tested | License | Commercial Use Permitted? |
|---|---|---|---|
| Python | 3.11+ / 3.14 | PSF License | Yes |
| FastAPI | 0.141+ | MIT | Yes |
| Uvicorn | 0.52+ | BSD-3-Clause | Yes |
| Pydantic | 2.13+ | MIT | Yes |
| FFmpeg / FFprobe | 7.1 / 8.0 | LGPL v2.1+ / GPL (essentials build) | Yes (LGPL builds recommended for dynamic linking, standard for containerized SaaS CLI) |
| static-ffmpeg | 3.0 | MIT | Yes |
| Pytest | 9.1+ | MIT | Yes |
| HTTPX | 0.28+ | BSD-3-Clause | Yes |
| Openpyxl | 3.1+ | MIT | Yes |
| OpenTimelineIO (native/schema) | Python OTIO / JSON-compatible | Apache 2.0 | Yes |

No AGPL or non-commercial (CC BY-NC) components exist in the default path.

---

## 4. Detailed Implementation Plan

1. **Step 1: OpenTimelineIO Export & Parser Extensions**
   - Implement `export_otio(timeline, video_meta)` in `app/timeline.py` producing standard OTIO schema JSON.
   - Add `/api/v1/sessions/{session_id}/otio` endpoint in `app/main.py`.
   - Extend `parser.py` and `engine.py` for caption color styling ("make that caption red"), speaker-based cuts, compound/atomic multi-part commands, and relative time expressions.
   - Add webhook signature dispatch for background jobs (`X-IncuBrix-Signature`).

2. **Step 2: 40+ Automated Scripted Scenario Test Suite**
   - Create `tests/test_scenarios_40.py` covering all 40+ required test scenarios with deterministic assertions.
   - Run the complete test suite and ensure 100% pass rate.

3. **Step 3: React + TypeScript + Vite + Tailwind CSS Frontend Studio**
   - Scaffold modern React application in `web/` with responsive dark-mode studio UI.
   - Build video player, interactive transcript with speaker pills, natural language prompt console, 3-way status badges, visual interactive timeline, edit history drawer, and render download manager.
   - Build frontend assets and serve them via FastAPI static mounts.

4. **Step 4: Scripted Sessions & Determinism Runs**
   - Execute all scripted sessions via `scripts/session_runner.py`.
   - Run 3 independent verification runs and compute SHA-256 determinism checks.
   - Generate renders and manifests.

5. **Step 5: Assessment Workbook & Documentation Updates**
   - Update `Assessment2_Rajala_Vishnu_Sathwick_Reddy.xlsx` with accurate, evidence-backed ratings and test paths.
   - Update `README.md`, `REPORT.md`, `SOURCES.md`, `AI_USE.md`, and `openapi.yaml`.
   - Package the entire deliverables pack into a distribution ZIP.

