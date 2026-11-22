# Suggested unedited demo recording (maximum 8 minutes)

Use a real MP4/MOV talking-head video that you own or have permission to process. Keep the recording continuous and unedited; the outline is a speaking guide, not a script to overstate functionality.

| Time | Show | Explain |
|---|---|---|
| 0:00–0:40 | Open the deployed IncuEdit studio; show service health and upload the licensed sample video. | State the source rights and that the uploaded original is never overwritten. |
| 0:40–1:30 | Supply a word-level transcript or use the configured transcription adapter; create a session. | Explain the transcript fields: word ID, source start/end, speaker and confidence. State any manual transcript correction. |
| 1:30–2:30 | Add a caption to an exact phrase, then cut content before it. | Open the timeline JSON and show that the caption stores word IDs rather than a fixed clock timestamp. Show that its rendered position follows the words. |
| 2:30–3:20 | Ask to remove a phrase that occurs more than once. | Show `needs_clarification`, the distinct occurrence options, and the user's explicit selection before any destructive edit. |
| 3:20–4:10 | Apply a low-confidence bleep request. | Show the confirmation question, confirm it, and play the generated bleep. Do not bleep a real person's voice without permission. |
| 4:10–5:00 | Upload a licensed background track and enable background music. | Show that the music ducks under the source audio and that the final audio stream is trimmed to the edited timeline. |
| 5:00–5:45 | Render the result; show the downloadable MP4 and `manifest.json`. | Point to the FFprobe stream-duration validation, source hash, rights attestation, settings, provider versions and warnings. |
| 5:45–6:45 | Run `python -m pytest -q` and `python scripts/session_runner.py examples/sessions --output artifacts/session_pack`. | Show the real command output and the 20-session evidence pack. Use the actual test count displayed at recording time. |
| 6:45–7:45 | Open `app/timeline.py` / `app/engine.py` and explain one design decision. | Explain source-range segments, stable word anchors, deterministic edit operations and why the LLM/parser does not own timeline state. |

Keep any known limitations visible and accurately describe them. The sample fixture shipped in this archive is synthetic and contains no spoken words; use a real consented video for the assessment demo and do not present synthetic transcript labels as diarisation results.
