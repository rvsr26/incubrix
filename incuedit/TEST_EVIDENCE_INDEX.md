# IncuEdit — Test Evidence & Verification Index

This document provides direct cross-references between every requirement in the official IncuBrix PS2 submission workbook (`Assessment2_Rajala_Vishnu_Sathwick_Reddy_FINAL.xlsx`) and the actual implementation files, automated tests, and reproducible artifacts.

---

## 1. Sheet 2 — Must-Haves Cross-Reference

| # | Must-Have Requirement | Status | Implementation File | Verification Test / Script | Output Evidence Path |
|---|---|---|---|---|---|
| **1** | **Never damage the original** (SHA-256 verified before/after; separate render) | **Yes** | `incuedit/app/main.py` `incuedit/app/render.py` | `incuedit/tests/test_api.py::test_upload_session_instruction_idempotency_and_render` | Upload source SHA-256 strictly preserved; isolated read-only processing |
| **2** | **Edits stick to content** (Captions, mutes, bleeps anchor to word IDs across cuts, reorders, restores) | **Yes** | `incuedit/app/timeline.py` `incuedit/app/engine.py` | `incuedit/tests/test_timeline.py` `incuedit/tests/test_scenarios_40.py` | `incuedit/artifacts/session_pack/session_18_results.json` `session_04_results.json` |
| **3** | **Three-way answers** (Strictly `applied`, `needs_clarification`, or `rejected`) | **Yes** | `incuedit/app/engine.py` `incuedit/app/models.py` | `incuedit/tests/test_engine.py` `incuedit/tests/test_scenarios_40.py` | Verified across all 38 session steps and 40 edge scenarios |
| **4** | **Predictable / Deterministic** (Same session produces identical timeline across runs) | **Yes** | `incuedit/app/timeline.py` `incuedit/scripts/verify_determinism.py` | `incuedit/scripts/verify_determinism.py` | `incuedit/artifacts/determinism_final/report.json` (20/20 sessions match across 3 rounds, 60 runs) |
| **5** | **Render matches timeline** (0 frames A/V offset and 0 frames length difference) | **Yes** | `incuedit/app/render.py` | `incuedit/scripts/package_and_verify.py` | `incuedit/artifacts/session_pack/*_manifest.json` (0.0 frames max offset) |
| **6** | **All core editing operations work** (cut, keep, reorder, speed 0.25x-4x, mute, bleep, caption, auto-caption, filler/silence removal, music with ducking, undo, redo, restore) | **Yes** | `incuedit/app/engine.py` `incuedit/app/timeline.py` | `incuedit/tests/test_timeline.py` `incuedit/tests/test_scenarios_40.py` | Verified programmatically across 110 automated tests |
| **7** | **Clear time policy** (`current_timeline` policy enforced throughout API & UI) | **Yes** | `incuedit/app/timeline.py` `incuedit/app/parser.py` | `incuedit/tests/test_timeline.py` | Visible timeline timestamps mapped explicitly to immutable source word spans |
| **8** | **Integration Standard followed** (Documented API, jobs, manifests, batch runner) | **Partial** | `incuedit/app/main.py` `incuedit/openapi.yaml` | `incuedit/scripts/validate_contract.py` `incuedit/scripts/session_runner.py` | 23/23 routes matched; local demo verified; public cloud hosting pending |

---

## 2. Sheet 3 — Levels Cross-Reference

| Level | Item | Status | Verification Evidence |
|---|---|---|---|
| **Core** | All must-haves pass | **Partial** | 7 of 8 Must-haves fully verified; Must-have 8 (Live Demo) is Partial |
| **Core** | 8-step worked example runs end-to-end | **Yes** | `incuedit/tests/test_api.py::test_upload_session_instruction_idempotency_and_render` |
| **Core** | Works on single-speaker video and transcript | **Yes** | `incuedit/examples/sessions/session_01.yaml` through `session_16.yaml` |
| **Advanced** | Edits that shift each other (captions, mutes, reorders) | **Yes** | `incuedit/tests/test_scenarios_40.py::test_scenario_01_caption_cut_sentence_restore_intro` |
| **Advanced** | Ambiguity & references ("that caption", "remove thanks") | **Yes** | `incuedit/tests/test_scenarios_40.py::test_scenario_05_remove_after_thanks_four_occurrences` |
| **Advanced** | Conflicts (repeated cuts, out of range, rollback) | **Yes** | `incuedit/tests/test_scenarios_40.py::test_scenario_03_duplicate_cut_and_out_of_range_and_time_formats` |
| **Advanced** | Two speakers ("remove what second speaker said") | **Partial** | `incuedit/tests/test_speaker_diarization.py` (Diarization provider interface; unknown speaker safety clarification) |
| **Outstanding** | Imperfect data (silence snapping, low-confidence words) | **Partial** | 80ms silence snapping implemented; low-confidence words ask clarification; real audio listening check unmeasured |
| **Outstanding** | Scale (60-minute video performance) | **No** | Tested only on short video fixtures (16s); 60m scale not verified on local machine |
| **Outstanding** | Export (OpenTimelineIO 1.0 schema) | **Yes** | `GET /api/v1/sessions/{id}/otio` verified in `incuedit/tests/test_api.py::test_otio_export` |
| **Outstanding** | Proof (Automated suite of 40+ scenarios) | **Yes** | `incuedit/tests/test_scenarios_40.py` (40 comprehensive edge-case scenarios) |

---

## 3. Sheet 6 — Hard Cases Cross-Reference

| Case # | Situation Description | System Action & Resolution | Automated Test Function | Artifact Evidence |
|---|---|---|---|---|
| **1** | Caption added, exact sentence cut, then cut restored | Caption anchored to word IDs; hidden during cut, restored with original timing upon restore | `test_scenario_01_caption_cut_sentence_restore_intro` | `incuedit/artifacts/session_pack/session_18_results.json` |
| **2** | Section reordered, word muted, filler cutting into bleeped word | Reordered segments preserve word-level audio effects; filler word trims around bleeps safely | `test_scenario_02_reorder_mute_filler_into_bleep` | `incuedit/artifacts/session_pack/session_04_results.json` |
| **3** | Duplicate cut sent; caption at 5:00 on short video; time formats | Duplicate cut returns `DUPLICATE_INSTRUCTION`; out-of-bounds returns `TIME_OUT_OF_RANGE`; time formats parse accurately | `test_scenario_03_duplicate_cut_and_out_of_range_and_time_formats` | `incuedit/artifacts/session_pack/session_09_results.json` `session_10_results.json` |
| **4** | "Undo second-to-last cut keep music"; "make bigger" without caption | Caption not found returns `CAPTION_NOT_FOUND`; restoring snapshot preserves independent background music | `test_scenario_04_undo_cut_keep_music_and_resize_without_caption` | `incuedit/artifacts/session_pack/session_19_results.json` |
| **5** | "Remove everything after I say thanks" where thanks said 4 times | Detects 4 occurrences and returns `needs_clarification` with timestamped options | `test_scenario_05_remove_after_thanks_four_occurrences` | `incuedit/app/engine.py` (lines 310–335) |
| **6** | "Speed up 10x", "cut everything", 3-part instruction where 1 fails | 10x rejected (`UNSUPPORTED_SPEED`); whole cut rejected (`WHOLE_VIDEO_CUT`); compound instructions roll back atomically | `test_scenario_06_unsupported_speed_whole_cut_and_compound_failure` | `incuedit/artifacts/session_pack/session_10_results.json` `session_11_results.json` |
| **7** | Two speakers, label swap, overlap, music ducking, VFR | Overlap detected and warned; music ducks under speech; VFR normalized via FFmpeg fps filter | `test_scenario_07_two_speaker_overlap_ducking_and_vfr` | `incuedit/artifacts/session_pack/session_17_manifest.json` |

---

## 4. Sheet 5 — Metrics Cross-Reference

| Metric | Measured Value | Measurement Basis | Evidence File |
|---|---|---|---|
| **Instruction Latency** | Median: 3.5 ms; Slowest: 9.0 ms | 38 instruction steps across 20 short scripted sessions (Windows 11 x64, Python 3.14.4) | `incuedit/artifacts/session_pack/results.json` |
| **Render Accuracy** | 0 frames A/V offset; 0 frames length difference | FFprobe stream analysis across 5 verified render manifests | `incuedit/artifacts/session_pack/*_manifest.json` |
| **Determinism** | 100.0% (20/20 sessions bitwise matched) | 3 independent runs across 20 sessions (60 executions, 0 hash mismatches) | `incuedit/artifacts/determinism_final/report.json` |
| **Clarification Quality** | 100% (2/2 ambiguous instructions asked clarification) | Scripted session runner (session 02 repeated phrase, session 16 low confidence) | `incuedit/artifacts/session_pack/session_02_results.json` `session_16_results.json` |
| **Word Clipping** | `Not measured` | Synthetic tone test fixtures; 80ms silence snapping padding applied on cut boundaries | `incuedit/REPORT.md` `incuedit/app/timeline.py` |
| **Cost** | USD $0.00 | Manual transcript + deterministic parser + local static FFmpeg | `incuedit/SOURCES.md` `incuedit/AI_USE.md` |
