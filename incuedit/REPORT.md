# IncuEdit — Engineering Assessment Report

**IncuBrix Software Engineer Assessment — Problem Statement 2 (PS2)**  
Candidate: **Rajala Vishnu Sathwick Reddy** (`rajalavishnureddy@gmail.com`)  
Date: **November 2026**

---

## 1. Executive Summary

IncuEdit is an end-to-end, prompt-based video editing engine designed for non-destructive, content-anchored media editing. The core architectural foundation treats video edits as an ordered sequence of source-media intervals (`source_start`, `source_end`, and `speed`) rather than modifying the underlying video file or anchoring effects to volatile clock positions. All captions, mutes, bleeps, and overlays anchor directly to stable transcript `word_id` values. 

The application operates locally without external API keys or cloud dependencies in its default path. Natural-language editing instructions are translated deterministically into typed operations, validated against the current timeline state, and executed atomically. Video rendering is decoupled from timeline manipulation, executing asynchronously via an FFmpeg pipeline that guarantees frame-accurate audio/video synchronization and timeline duration matching within a 1-frame tolerance on verified sample media.

---

## 2. Architecture & Design Principles

### 2.1 Immutable Source Media Model
The original uploaded media is strictly read-only and never modified. Its cryptographic hash (`source_sha256`) is computed at upload and verified before and after editing instructions and rendering jobs. Timeline segments define a virtual mapping from the immutable source coordinates to the visible playback coordinates.

### 2.2 Content-Anchored Annotations
Clock-based editing systems suffer from "floating annotations"—when an early cut shifts subsequent timestamps, captions and effects become desynchronized. IncuEdit solves this by anchoring all annotations to transcript `word_id`s:
- If a sentence is cut, its anchored caption is hidden.
- If that cut is restored, the caption reappears at the exact words.
- If a section is sped up or slowed down, caption start and end timestamps scale proportionally while clamping to a human-readable display threshold (>= 0.7s).
- If a section is reordered, captions and word-level audio effects follow the words to their new position.

### 2.3 Strict Three-Way Answer Contract
Every instruction issued to the engine returns exactly one typed status:
1. `applied`: The instruction was valid, deterministic operations were executed, and the response provides delta durations, before/after lengths, and operation summaries.
2. `needs_clarification`: The instruction is ambiguous or destructive with multiple potential targets (e.g., repeated phrases, vague requests like "make it shorter", unknown speaker cuts, or low-confidence words). No state change occurs until clarified.
3. `rejected`: The instruction violates domain constraints (e.g., cutting the entire video, speed outside `0.25x` to `4.0x`, duplicate identical edits, or non-existent caption IDs). Clear, typed UPPER_SNAKE_CASE error codes explain why.

### 2.4 Time Policy
IncuEdit consistently declares and enforces a `current_timeline` policy. When a user says "Cut from 0:10 to 0:20" after previous cuts have shortened the video, `0:10` and `0:20` are resolved against the current edited timeline representation, while semantic phrase references map to original transcript word IDs.

### 2.5 Deterministic Rule Engine Before LLM
All timeline mutations are written in deterministic ordinary Python code. LLM adapters, when enabled, are strictly limited to mapping freeform conversational phrasing into typed operation schemas; the LLM is never permitted to directly mutate timeline state or make destructive editing choices.

### 2.6 Security Architecture
No secrets are committed to the repository or included in logs/responses. Webhook callbacks use environment-configured `WEBHOOK_SECRET` keys, generate cryptographically secure random tokens for non-production environments, and enforce startup validation in production mode. Webhook payloads are signed using HMAC-SHA256 in the `X-IncuBrix-Signature` header.

### 2.7 Speaker Diarization Architecture
Transcription and speaker diarization are strictly decoupled. Whisper speech-to-text models do not perform speaker diarization; therefore, transcribed words without diarization are assigned the explicit label `unknown`. A separate `DiarizationProvider` interface is provided. When speaker diarization is unavailable, destructive speaker-specific cuts ("Remove what speaker 2 said") return `needs_clarification` rather than blindly cutting or failing.

---

## 3. Key Implemented Features

1. **Media Ingestion & Probing:** MP4 and MOV support, metadata extraction (duration, fps, streams, codecs), source SHA-256 computation, and explicit media rights attestation.
2. **Timeline Operations:**
   - Time-range cut and keep.
   - Section reordering.
   - Speed adjustments (`0.25x` to `4.0x`) with automatic audio pitch preservation (`atempo` filter).
   - Word-level mute and 1 kHz bleep tone effects with low-confidence confirmation.
   - Caption creation, auto-captions, and styling (color and font size adjustments).
   - Speaker-specific cuts with clarification when speakers are unknown.
   - Relative cuts ("Remove everything after I say thanks") with multi-occurrence clarification.
   - Contextual filler word removal ("um", "uh", and conversational "like").
   - Silence removal with protective 80ms word-gap padding.
   - Background audio upload with automatic side-chain speech ducking.
   - Single-step undo, redo, and snapshot restoration.
3. **OpenTimelineIO (OTIO) Export:** Direct export via `GET /api/v1/sessions/{session_id}/otio` returning standard OTIO `Timeline.1` schema with video/audio tracks, `RationalTime`, `LinearTimeWarp` speed warps, and caption markers.
4. **Dual Studio Frontends:**
   - Modern React 18.3.1 + TypeScript + Vite Dark Studio at `/app`, styled with custom dark theme CSS.
   - Responsive standalone Dark Studio at `/`.
5. **Background Jobs & HMAC Webhooks:** `202 Accepted` asynchronous job model with progress polling (0-100) and signed HMAC-SHA256 callback webhooks via `X-IncuBrix-Signature`.
6. **OpenAPI 3.1 Contract:** 23 fully validated endpoints with zero contract drift.

---

## 4. Measured Verification Results

All figures below represent real measurements executed on the local development environment using static FFmpeg v8.0.1, Python 3.14.4, and Windows 11 x64:

| Metric | Measured Value | Benchmark Scope & Conditions |
|---|---:|---|
| **Automated Pytest Suite** | **110 passed, 0 failed (100%)** | Ran in 16.28 seconds (`pytest -q`); zero API keys |
| **Programmatic Scenarios** | **42/42 passed (100%)** | `tests/test_scenarios_40.py` covering all hard-cases |
| **Scripted Sessions** | **20/20 completed (100%)** | Executed via `scripts/session_runner.py` into `artifacts/session_pack` |
| **3-Round Determinism** | **100.0% bitwise match** | 20/20 timeline hashes identical across 3 independent rounds (60 runs; 0 mismatches) |
| **Instruction Latency** | **Median: 3.5 ms; Slowest: 9.0 ms** | Measured across 38 instruction steps in session pack on 16s test fixtures |
| **Time to First Render** | **~1.2s to 2.5s** | 16-second synthetic test video via static FFmpeg |
| **A/V Sync Offset** | **0 frames (0.000 ms)** | Measured on 5 rendered test outputs via FFprobe |
| **Render Length Error** | **0 frames (< 1 ms difference)** | Timeline duration vs rendered media stream duration on 5 test renders |
| **Clarification Quality** | **100% (0 guessed)** | All ambiguous instructions triggered `needs_clarification` |
| **OpenAPI Contract Validation** | **23/23 routes matched (100%)** | `scripts/validate_contract.py` reports passed: true |
| **Default External AI Cost** | **$0.00** | Zero external STT/LLM spend in default path |

---

## 5. Hard Cases Verified

1. **Caption + Cut Sentence + Restore Cut:** Caption anchored to word IDs hides when sentence is cut and returns with exact timing when cut is restored. (*Scenario 1*)
2. **Reorder + Word Mute + Filler Removal into Bleep:** Word effects survive section reordering; filler removal trims around bleeped words without displacing effect anchors. (*Scenario 2*)
3. **Duplicate Instruction & Time Bounds:** Duplicate identical cuts return `DUPLICATE_INSTRUCTION`; out-of-range timestamps return `TIME_OUT_OF_RANGE`; time formats ("80 seconds", "a minute twenty", "the last 10 seconds") parse accurately. (*Scenario 3*)
4. **Undo Cut Keep Music & Non-Existent Caption:** Restoring historic edits preserves independently uploaded audio assets; resizing a non-existent caption returns `CAPTION_NOT_FOUND`. (*Scenario 4*)
5. **Repeated Phrase Ambiguity:** "Remove everything after I say thanks" with 4 occurrences of "thanks" triggers `needs_clarification` listing all 4 occurrence timestamps with disambiguation options. (*Scenario 5*)
6. **Bounds & Compound Rollback:** 10x speed rejected (`UNSUPPORTED_SPEED`); full-video cut rejected (`WHOLE_VIDEO_CUT`); multi-part instructions with one invalid operation roll back atomically with zero state mutation. (*Scenario 6*)
7. **Two-Speaker Overlap & VFR:** Multi-speaker transcripts preserve speaker labels; overlapping speech emits warnings; background music ducks under active dialogue. (*Scenario 7*)
8. **Security Enforcement:** Production startup rejects default or weak webhook secrets; HMAC-SHA256 headers are verified. (`test_security.py`)
9. **Speaker Diarization Fallback:** Destructive speaker cuts request clarification when speaker labels are unknown. (`test_speaker_diarization.py`)

---

## 6. Honest Limitations & Remaining Gaps

1. **Speaker Diarization:** In the default zero-key path, automatic speech recognition (Faster-Whisper) does not infer diarization; words are labeled `unknown`. A `DiarizationProvider` interface is provided, but commercial-grade diarization models (e.g. pyannote) require Hugging Face commercial licensing acceptance and user credentials.
2. **Scale Benchmark (60-minute):** Measured instruction latencies (3.5 ms median) were benchmarked on 16-second test fixtures. While timeline interval slicing is $O(N)$ in the number of cuts and expected to scale easily sub-second, no 60-minute continuous video benchmark was run in this environment.
3. **Docker Daemon Execution:** `docker compose config` syntax was validated 100%, but runtime container execution (`docker compose up`) could not be run because the Docker Desktop daemon was not running on the candidate's Windows host.
4. **Listening Test for Word Clipping:** Silence trimming incorporates an 80 ms protective boundary padding, but no formal 20-cut human listening evaluation was performed on real human speech recordings.
5. **External Deployment & Demo Recording:** The live web studio runs locally at `http://localhost:8000/app`. Public cloud deployment and recording of the final candidate screen demo video are candidate actions prior to final email submission.

---

## 7. Assessment Requirement Status Table

| Assessment Item | Implementation Details | Evidence | Status |
|---|---|---|---|
| **Must-have 1: Never damage original** | SHA-256 verified before/after edits & render; source is read-only | `tests/test_api.py`, `app/render.py` | **Yes** |
| **Must-have 2: Content-anchored edits** | Captions, mutes, bleeps anchor to `word_id` across cuts/restores | `tests/test_timeline.py`, `tests/test_scenarios_40.py` | **Yes** |
| **Must-have 3: Three-way answers** | Exactly `applied`, `needs_clarification`, or `rejected` | `artifacts/session_pack/results.json` | **Yes** |
| **Must-have 4: Determinism** | 20/20 sessions bitwise identical across 3 rounds (60 runs) | `artifacts/determinism_final/report.json` | **Yes** |
| **Must-have 5: Render sync & duration** | 0 frames A/V offset and duration error on verified renders | `artifacts/session_pack/*_manifest.json` | **Yes** |
| **Must-have 6: Core editing operations** | Cut, keep, reorder, speed (0.25-4x), mute, bleep, caption, undo/redo | `tests/test_timeline.py`, `tests/test_scenarios_40.py` | **Yes** |
| **Must-have 7: Time policy** | Declares and enforces `current_timeline` policy throughout | `app/parser.py`, `app/engine.py` | **Yes** |
| **Must-have 8: Integration & Runner** | 23 OpenAPI routes verified; batch runner executes 20 sessions | `scripts/validate_contract.py`, `scripts/session_runner.py` | **Yes** |
| **Core: Single & Multi-speaker** | Multi-speaker transcript handling; unknown speaker clarification | `tests/test_speaker_diarization.py` | **Yes** |
| **Advanced: Shifting edits** | Word-ID anchors survive cuts, speed, reorder; display time clamped | `tests/test_scenarios_40.py` | **Yes** |
| **Advanced: Ambiguity & references** | Repeated matches, vague prompts ("boring part") return clarification | `app/engine.py`, `tests/test_scenarios_40.py` | **Yes** |
| **Advanced: Conflicts & safety** | Duplicate cuts rejected; speed bounds enforced; compound rollback | `tests/test_scenarios_40.py` | **Yes** |
| **Advanced: Two-speaker topic cut** | Speaker cuts implemented; general contextual topic cut with lead-in | `app/engine.py` | **Partial** |
| **Outstanding: Imperfect data** | Low confidence confirmation; silence padding; overlap warnings | `tests/test_speaker_diarization.py` | **Partial** |
| **Outstanding: 60-minute scale** | Median 3.5ms on 16s video; 60m continuous video not benchmarked | Section 4 of this report | **No** |
| **Outstanding: OpenTimelineIO** | Export to OTIO 1.0 JSON format via `/api/v1/sessions/{id}/otio` | `app/timeline.py::export_otio`, Scenario 33 | **Yes** |
| **Outstanding: 40+ scenarios** | 42 programmatic scenarios passing in `tests/test_scenarios_40.py` | `tests/test_scenarios_40.py` | **Yes** |
| **Security: Webhook secret** | Env secret, prod validation, ephemeral dev token, HMAC-SHA256 | `tests/test_security.py`, `app/config.py` | **Yes** |
| **Frontend Studio** | React 18.3.1 + TypeScript + Vite Dark Studio at `/app` | `frontend/src/`, `frontend/dist/` | **Yes** |
