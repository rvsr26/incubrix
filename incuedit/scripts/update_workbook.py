"""Update Assessment2_Rajala_Vishnu_Sathwick_Reddy.xlsx with accurate, honest, and properly mapped results."""
import openpyxl
from pathlib import Path

def update_file(wb_path: Path):
    if not wb_path.exists():
        return
    print(f"Updating {wb_path} ...")
    wb = openpyxl.load_workbook(wb_path)

    # 1_Your_Details
    s1 = wb["1_Your_Details"]
    s1["B4"] = "RAJALA VISHNU SATHWICK REDDY"
    s1["B5"] = "rajalavishnureddy@gmail.com"
    s1["B6"] = "9390934449"
    s1["B7"] = "Amrita Vishwa Vidyapeetham, Coimbatore — B.Tech, Computer Science and Engineering"
    s1["B8"] = 2027
    s1["B9"] = "http://localhost:8000/app (React Studio) & http://localhost:8000 (Dark Studio)"
    s1["B10"] = "Not applicable — open local review"
    s1["B11"] = "< 50 ms local start"
    s1["B12"] = "https://github.com/VishnuSathwickReddy/incuedit (private repo; invite upon request)"
    s1["B13"] = "DEMO_RECORDING_SCRIPT.md (in repository root)"
    s1["B14"] = "incuedit/REPORT.md"
    s1["B15"] = "Windows 11 x64, Intel Core i7, Python 3.14.4, static FFmpeg v8.0.1"
    s1["B16"] = "No paid APIs/services used; $0 external-service spend"
    s1["B17"] = "ChatGPT & Antigravity (see AI_USE.md)"
    s1["B18"] = 38

    # 2_Must_haves
    s2 = wb["2_Must_haves"]
    # Row 6: Never damage the original
    s2["C6"] = "Yes"
    s2["D6"] = "incuedit/tests/test_api.py::test_upload_session_instruction_idempotency_and_render ; incuedit/tests/test_scenarios_40.py ; incuedit/app/main.py ; incuedit/app/render.py"
    s2["E6"] = "Upload source SHA-256 is immutable and strictly verified before and after edits/render; render engine runs isolated read-only."

    # Row 7: Edits stick to content
    s2["C7"] = "Yes"
    s2["D7"] = "incuedit/app/timeline.py ; incuedit/tests/test_timeline.py ; incuedit/tests/test_scenarios_40.py ; incuedit/artifacts/session_pack/results.json ; sessions 01, 07, 18"
    s2["E7"] = "Captions, mutes, bleeps, and speed warps anchor to transcript word_id values; mappings adjust dynamically across cuts, restores, and reorders."

    # Row 8: Three-way answers
    s2["C8"] = "Yes"
    s2["D8"] = "incuedit/artifacts/session_pack/results.json ; incuedit/tests/test_scenarios_40.py ; incuedit/app/engine.py"
    s2["E8"] = "Every instruction returns strictly one status: applied, needs_clarification, or rejected. Verified across all 38 session steps and 42 programmatic scenarios."

    # Row 9: Predictable
    s2["C9"] = "Yes"
    s2["D9"] = "incuedit/artifacts/determinism_final/report.json ; incuedit/artifacts/determinism_final/round1-3/results.json ; incuedit/app/engine.py ; incuedit/app/timeline.py"
    s2["E9"] = "100% bitwise determinism verified: 20/20 sessions produce identical timeline hashes across 3 consecutive independent rounds (60 runs; 0 mismatches)."

    # Row 10: Render matches timeline
    s2["C10"] = "Yes"
    s2["D10"] = "incuedit/artifacts/session_pack/session_01_manifest.json ; session_16_manifest.json ; session_17_manifest.json ; session_19_manifest.json ; session_20_manifest.json ; incuedit/tests/test_api.py"
    s2["E10"] = "Frame-accurate FFmpeg pipeline verified with 0-frame A/V offset and 0-frame timeline length error across 5 verified test renders."

    # Row 11: All operations work
    s2["C11"] = "Yes"
    s2["D11"] = "incuedit/app/engine.py ; incuedit/app/timeline.py ; incuedit/tests/test_timeline.py ; incuedit/tests/test_scenarios_40.py ; incuedit/artifacts/session_pack/session_06_results.json ; session_07_results.json ; session_19_results.json"
    s2["E11"] = "Cut, keep, reorder, speed (0.25x-4x), mute, bleep, caption, auto-caption, filler removal, silence removal, background music with ducking, undo, redo, and restore specific edit number all verified."

    # Row 12: Clear time policy
    s2["C12"] = "Yes"
    s2["D12"] = "incuedit/app/parser.py ; incuedit/app/engine.py ; incuedit/artifacts/session_pack/ ; README.md"
    s2["E12"] = "Declares and enforces current_timeline time policy across the entire API and UI. Numeric timestamps reference visible timeline; words anchor to source word_id."

    # Row 13: Integration Standard followed
    s2["C13"] = "Partial"
    s2["D13"] = "incuedit/openapi.yaml ; incuedit/scripts/session_runner.py ; incuedit/docker-compose.yml ; incuedit/README.md ; incuedit/artifacts/session_pack/results.json"
    s2["E13"] = "Contract validation passes 23/23 routes with zero drift. Automated batch session runner verifies 20/20 sessions. Local server works; Docker daemon was not running in test environment."

    # 3_Levels
    s3 = wb["3_Levels"]
    # Core
    s3["C5"] = "Yes"
    s3["D5"] = "incuedit/2_Must_haves rows 1-8 ; 100+ pytest tests passing ; artifacts/session_pack/results.json ; artifacts/determinism_final/report.json"
    s3["E5"] = "Run `python -m pytest -q` (100+ passed); `python scripts/session_runner.py examples/sessions --output artifacts/session_pack`; open http://localhost:8000/app"

    s3["C6"] = "Yes"
    s3["D6"] = "incuedit/artifacts/session_pack/session_01_results.json ; incuedit/examples/sessions/session_01.yaml ; incuedit/tests/test_scenarios_40.py"
    s3["E6"] = "Run `python scripts/session_runner.py examples/sessions/session_01.yaml` to run all cut, keep, speed, bleep, caption, undo steps"

    s3["C7"] = "Yes"
    s3["D7"] = "incuedit/examples/sample_transcript.json ; incuedit/tests/test_scenarios_40.py (scenario 7, 31) ; incuedit/app/engine.py"
    s3["E7"] = "`pytest -k test_scenario_07_two_speaker_overlap_ducking_and_vfr` verifies multi-speaker parsing and timeline handling"

    # Advanced
    s3["C8"] = "Yes"
    s3["D8"] = "incuedit/app/timeline.py ; incuedit/tests/test_scenarios_40.py (scenarios 1, 2, 8, 14, 15) ; sessions 01/07/18"
    s3["E8"] = "Captions follow words across cuts, reorders, and speed changes; partial cuts maintain valid anchor intervals; minimum display time clamped"

    s3["C9"] = "Yes"
    s3["D9"] = "incuedit/app/engine.py ; incuedit/app/parser.py ; incuedit/tests/test_scenarios_40.py (scenarios 18-24)"
    s3["E9"] = "'that caption', 'boring part', 'make it shorter', repeated occurrences all return NEEDS_CLARIFICATION; synonym matching implemented"

    s3["C10"] = "Yes"
    s3["D10"] = "incuedit/app/engine.py ; incuedit/tests/test_scenarios_40.py (scenarios 25-30)"
    s3["E10"] = "Repeated operations rejected as DUPLICATE_INSTRUCTION; pause preservation; whole-video cut rejected; speed bounds enforced; compound rollback atomic"

    s3["C11"] = "Partial"
    s3["D11"] = "incuedit/app/engine.py ; incuedit/app/parser.py ; incuedit/tests/test_scenarios_40.py (scenario 31)"
    s3["E11"] = "'Remove what speaker 2 said' cuts speaker 2 segments; general contextual job topic removal with lead-in question clarification is partial"

    # Outstanding
    s3["C12"] = "Partial"
    s3["D12"] = "incuedit/app/engine.py ; incuedit/app/render.py ; incuedit/tests/test_scenarios_40.py (scenarios 16, 17, 32)"
    s3["E12"] = "Silence snapping prevents word clipping; low-confidence words require clarification; overlap warned; real VFR/diarization swap is partial"

    s3["C13"] = "No"
    s3["D13"] = "incuedit/REPORT.md ; incuedit/app/engine.py"
    s3["E13"] = "Not measured on a 60-minute video. Median 3.5ms on 16s video; 60m scale not benchmarked."

    s3["C14"] = "Yes"
    s3["D14"] = "incuedit/app/timeline.py (export_otio) ; incuedit/app/main.py (/otio) ; tests/test_scenarios_40.py (scenario 33)"
    s3["E14"] = "Run `GET /api/v1/sessions/{id}/otio` to export valid OpenTimelineIO 1.0 schema with tracks, markers, and linear time warps"

    s3["C15"] = "Yes"
    s3["D15"] = "incuedit/tests/test_scenarios_40.py ; 100+ pytest tests"
    s3["E15"] = "Run `python -m pytest tests/test_scenarios_40.py -v` to execute all 42 automated scenarios with 100% pass rate"

    # 4_Integration
    s4 = wb["4_Integration"]
    # Point 1: One-command start and test
    s4["C5"] = "Partial"
    s4["D5"] = "incuedit/Dockerfile ; incuedit/docker-compose.yml ; incuedit/.env.example ; `python -m pytest -q` -> passed with 0 API keys. Docker daemon was not running on host."

    # Point 2: Documented HTTP API
    s4["C6"] = "Yes"
    s4["D6"] = "incuedit/openapi.yaml ; incuedit/scripts/validate_contract.py. OpenAPI 3.1 contract covers all 23 FastAPI paths and methods with 100% match."

    # Point 3: Background jobs
    s4["C7"] = "Yes"
    s4["D7"] = "incuedit/app/main.py ; incuedit/artifacts/session_pack/session_01_results.json. 202 Accepted, job status polling, progress 0-100, and HMAC-SHA256 signed callback URL via X-IncuBrix-Signature header."

    # Point 4: Safe retries
    s4["C8"] = "Yes"
    s4["D8"] = "incuedit/app/main.py ; incuedit/tests/test_api.py::test_upload_session_instruction_idempotency_and_render. Idempotency-Key enforced on all POST endpoints."

    # Point 5: Clear errors
    s4["C9"] = "Yes"
    s4["D9"] = "incuedit/app/errors.py ; incuedit/README.md ; incuedit/tests/test_api.py. UPPER_SNAKE_CASE error codes with retryable and details."

    # Point 6: Configuration
    s4["C10"] = "Yes"
    s4["D10"] = "incuedit/app/config.py ; incuedit/.env.example ; incuedit/README.md. All paths, limits, provider types, and secrets loaded from environment variables."

    # Point 7: Files in, files out
    s4["C11"] = "Partial"
    s4["D11"] = "incuedit/app/main.py ; incuedit/app/storage.py ; incuedit/docker-compose.yml. Direct upload and HTTPS import verified; MinIO S3 adapter code present but Docker unverified on host."

    # Point 8: Logs and health
    s4["C12"] = "Yes"
    s4["D12"] = "incuedit/app/main.py ; incuedit/artifacts/session_pack/results.json. Structured JSON logs with timestamp, level, job_id, correlation_id; /health and /ready routes."

    # Point 9: Output manifest
    s4["C13"] = "Yes"
    s4["D13"] = "incuedit/app/render.py ; incuedit/artifacts/session_pack/session_01_manifest.json. Includes input/output sha256, duration, offset, settings, timings, rights."

    # Point 10: Batch runner
    s4["C14"] = "Yes"
    s4["D14"] = "incuedit/scripts/session_runner.py ; incuedit/artifacts/session_pack/results.json. CLI runner executes file or full directory with per-session artifacts."

    # 5_Metrics - STRICT CORRECTION ACCORDING TO ACTUAL HEADINGS
    s5 = wb["5_Metrics"]
    # Row 5: Instruction latency
    s5["C5"] = "Median: 3.5 ms; Slowest: 9.0 ms (short 16s fixtures; 60m not measured)"
    s5["D5"] = "Windows 11 x64, Python 3.14.4, 38 instruction steps across 20 short sessions"
    s5["E5"] = "incuedit/artifacts/session_pack/*_results.json ; incuedit/REPORT.md"

    # Row 6: Render accuracy (Largest A/V offset and largest length difference)
    s5["C6"] = "0 frames A/V offset; 0 frames length difference (for 5 verified sample renders)"
    s5["D6"] = "Programmatic FFprobe encoded audio/video stream duration comparison on 5 test renders"
    s5["E6"] = "incuedit/artifacts/session_pack/*_manifest.json"

    # Row 7: Determinism (Share of sessions with identical timeline_hash across 3 runs)
    s5["C7"] = "100.0% (20/20 sessions matched across 3 rounds, 60 executions)"
    s5["D7"] = "3 independent runner rounds on local environment (Windows 11 x64)"
    s5["E7"] = "incuedit/artifacts/determinism_final/report.json"

    # Row 8: Clarification quality (How many ambiguous instructions asked or stated an assumption, versus guessed)
    s5["C8"] = "100% (2 ambiguous instructions in session pack asked for clarification; 0 guessed)"
    s5["D8"] = "Scripted session pack runner (session 02 repeated phrase, session 16 low confidence)"
    s5["E8"] = "incuedit/artifacts/session_pack/session_02_results.json ; session_16_results.json"

    # Row 9: Word clipping (Number of cuts that clip part of a word, from a listening check of 20 cuts)
    s5["C9"] = "Not measured (synthetic tone media; 80ms silence padding applied on cut boundaries)"
    s5["D9"] = "Synthetic test fixtures; no human listening panel evaluation on real speech"
    s5["E9"] = "incuedit/REPORT.md ; incuedit/app/timeline.py"

    # Row 10: Cost (Speech-to-text and language-model cost per minute of video edited)
    s5["C10"] = "$0.00 external STT/LLM API spend in default path"
    s5["D10"] = "Manual transcript + deterministic parser + local static FFmpeg"
    s5["E10"] = "incuedit/SOURCES.md ; incuedit/AI_USE.md ; incuedit/REPORT.md"

    # Clear dangling rows 11 to 15 in 5_Metrics
    for r in range(11, 16):
        for col in ["A", "B", "C", "D", "E"]:
            s5[f"{col}{r}"].value = None

    # 6_Hard_cases
    s6 = wb["6_Hard_cases"]
    s6["C5"] = "Yes"
    s6["D5"] = "Caption is anchored to word IDs; a cut hides it and restoring the source interval makes it visible again with exact original timing."
    s6["E5"] = "incuedit/tests/test_scenarios_40.py::test_scenario_01_caption_cut_sentence_restore_intro ; incuedit/artifacts/session_pack/session_18_results.json"

    s6["C6"] = "Yes"
    s6["D6"] = "Reordered segments preserve word-level audio effects; filler word removal correctly trims around bleeped words without removing audio effect anchors."
    s6["E6"] = "incuedit/tests/test_scenarios_40.py::test_scenario_02_reorder_mute_filler_into_bleep ; incuedit/artifacts/session_pack/session_04_results.json"

    s6["C7"] = "Yes"
    s6["D7"] = "Duplicate cut returns REJECTED (DUPLICATE_INSTRUCTION); caption at 5:00 on short video returns REJECTED (TIME_OUT_OF_RANGE); '80 seconds', 'a minute twenty', 'the last 10 seconds' all parse accurately."
    s6["E7"] = "incuedit/tests/test_scenarios_40.py::test_scenario_03_duplicate_cut_and_out_of_range_and_time_formats ; incuedit/artifacts/session_pack/session_09_results.json ; session_10_results.json"

    s6["C8"] = "Yes"
    s6["D8"] = "'make it bigger' when no caption exists returns REJECTED (CAPTION_NOT_FOUND); restore specific history snapshot restores timeline without wiping independent audio track."
    s6["E8"] = "incuedit/tests/test_scenarios_40.py::test_scenario_04_undo_cut_keep_music_and_resize_without_caption ; incuedit/artifacts/session_pack/session_19_results.json"

    s6["C9"] = "Yes"
    s6["D9"] = "Detects 4 matches for 'thanks' and returns NEEDS_CLARIFICATION listing all 4 occurrence timestamps with options for user disambiguation."
    s6["E9"] = "incuedit/tests/test_scenarios_40.py::test_scenario_05_remove_after_thanks_four_occurrences ; incuedit/app/engine.py"

    s6["C10"] = "Yes"
    s6["D10"] = "10x speed rejected (UNSUPPORTED_SPEED); full-video cut rejected (WHOLE_VIDEO_CUT); compound 3-part instruction with 1 invalid operation rolls back atomically with no partial application."
    s6["E10"] = "incuedit/tests/test_scenarios_40.py::test_scenario_06_unsupported_speed_whole_cut_and_compound_failure ; incuedit/artifacts/session_pack/session_10_results.json ; session_11_results.json"

    s6["C11"] = "Yes"
    s6["D11"] = "Two-speaker timeline preserves speaker IDs; overlapping speech triggers warning; music ducks under active speech; VFR rate handled gracefully."
    s6["E11"] = "incuedit/tests/test_scenarios_40.py::test_scenario_07_two_speaker_overlap_ducking_and_vfr ; incuedit/artifacts/session_pack/session_17_manifest.json"

    # 7_Declaration - COMPLETELY BLANK FOR CANDIDATE REVIEW & PERSONAL SIGNING
    s7 = wb["7_Declaration"]
    for r in range(4, 14):
        s7[f"B{r}"].value = None

    wb.save(wb_path)
    print(f"Successfully saved {wb_path}")

update_file(Path("Assessment2_Rajala_Vishnu_Sathwick_Reddy.xlsx"))
update_file(Path("IncuEdit_PS2_Complete_Project/incuedit/Assessment2_Rajala_Vishnu_Sathwick_Reddy.xlsx"))
