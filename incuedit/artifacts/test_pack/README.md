# IncuEdit test pack index

- `../session_pack/` contains the final 20-session evidence run, per-step responses, timeline JSON files, rendered MP4s for render scenarios, manifests, and the aggregate `results.json`.
- `../determinism_final/round1` through `round3` contain 20 session result sets from three independently restarted API processes (60 independent session runs). All 20 hashes match across the three rounds; there are 0 mismatches.
- `failures/session_16_yaml_boolean_answer_before_fix.json` records a runner failure discovered before the YAML boolean normalisation fix. The issue was in the CLI conversion of YAML `yes` to a boolean string, not the editing engine. The runner now normalises YAML `true` to the answer `yes`, and regression tests cover true/false/text/none. The final session_16 run now produces `needs_clarification` then `applied` and renders successfully.
- The current test suite reports 56 passing tests with `python -m pytest -q`. The final batch contains 20/20 completed sessions and 38 instruction steps (32 applied, 2 needs_clarification, 4 rejected).

All media is synthetic. The sample video contains no speech; the synthetic transcript is for validating timeline behavior only.
