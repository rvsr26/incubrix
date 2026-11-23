# IncuEdit — Practical Demo Recording Script (Max 8 Minutes, Unedited)

**Candidate:** RAJALA VISHNU SATHWICK REDDY  
**Assessment:** IncuBrix Software Engineer Assessment — Problem Statement 2 (IncuEdit)  
**Rule:** Continuous, unedited single-take recording under 8:00 minutes.

---

## Pre-Recording Setup (2 minutes before starting)

1. Open a terminal and start the IncuEdit server:
   ```bash
   cd incuedit
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. Open Chrome to `http://localhost:8000/app/` (React Studio UI).
3. Open a second browser tab to `http://localhost:8000/docs` (FastAPI Swagger UI).
4. Open VS Code showing `app/timeline.py` in the background.
5. Have your screen recorder ready (OBS Studio or Windows Game Bar `Win + G`).

---

## 8-Minute Step-by-Step Recording Timeline

### 0:00 – 0:30 | 1. Introduction & Overview
- **Visual:** Face webcam (optional) and IncuEdit React Studio interface (`http://localhost:8000/app/`).
- **Speaking Points:**
  - *"Hi, I'm Rajala Vishnu Sathwick Reddy, presenting IncuEdit for the IncuBrix Software Engineer Assessment, Problem Statement 2."*
  - *"IncuEdit is a prompt-based video editing engine built on a non-destructive, immutable source-media model. It guarantees 100% determinism, exact audio/video synchronization, and content-anchored effects that never drift when video is cut or reordered."*

### 0:30 – 1:15 | 2. Upload Video & Show Metadata Immutability
- **Action:** Click **"Load Demo Video"** (or upload `examples/demo_media.mp4`).
- **Speaking Points:**
  - *"Notice the video metadata displayed: duration 16.0s, resolution 640x360, 25 fps, and the source SHA-256 hash."*
  - *"The source video file is completely immutable. Every editing operation creates a new timeline state in memory; the original file is never modified or overwritten."*

### 1:15 – 2:15 | 3. Transcript & Stable Word Anchors
- **Action:** Click **"Create Session"** to load the transcript. Point to the word chip list in the UI.
- **Speaking Points:**
  - *"Here is the synchronized transcript. Each word has a unique, stable `word_id` and source start/end timestamps."*
  - *"Effects like captions, mutes, and bleeps anchor to these persistent word IDs, rather than floating clock times. This means if we cut 5 seconds before a caption, the caption stays attached to the exact word where it was placed."*

### 2:15 – 3:30 | 4. Apply Editing Instructions (Cut, Caption, Bleep)
- **Action:** 
  1. Type or click preset: `"Add caption 'Welcome to IncuEdit' at 2.0s"` → Click **Apply**.
  2. Type or click preset: `"Cut the first 2 seconds"` → Click **Apply**.
  3. Type or click preset: `"Bleep the word secret"` → Click **Apply**.
- **Speaking Points:**
  - *"Notice that when we cut the first 2 seconds, the timeline duration updates from 16.0s to 14.0s."*
  - *"The caption 'Welcome to IncuEdit' did not disappear or drift to the wrong place — its timeline position automatically adjusted because it's anchored to content."*
  - *"The word 'secret' now has an attached bleep audio effect filter."*

### 3:30 – 4:15 | 5. Ambiguous Instruction & Clarification
- **Action:** Type: `"Remove everything after I say thanks"` (a phrase that appears multiple times in the transcript).
- **Speaking Points:**
  - *"Now I'll test an ambiguous instruction where 'thanks' appears at multiple timestamps."*
  - *"Instead of guessing or making a destructive mistake, IncuEdit returns `needs_clarification`."*
  - *"The UI displays the disambiguation prompt with each occurrence timestamp so the user can choose explicitly."*

### 4:15 – 5:00 | 6. Undo, Redo, and Restoring Earlier Edit
- **Action:** Click **"Undo"**, then click **"Redo"**, then click **"Restore Edit #1"**.
- **Speaking Points:**
  - *"IncuEdit maintains a versioned DAG history. Clicking Undo instantly steps back to the previous timeline state without touching disk."*
  - *"Clicking Redo re-applies the edit. We can also restore any arbitrary snapshot from history, and all word anchors and background tracks are preserved."*

### 5:00 – 6:15 | 7. Render Video & Job Progress
- **Action:** Click **"Render Video"**.
- **Speaking Points:**
  - *"Rendering is asynchronous. The POST request returns HTTP 202 Accepted with a unique `job_id`."*
  - *"The UI polls `GET /api/v1/jobs/{job_id}`, showing progress from 0% to 100%."*
  - *"The rendering pipeline uses an isolated FFmpeg filtergraph to stitch segments, apply audio ducking, render captions, and ensure exact frame alignment."*

### 6:15 – 7:00 | 8. Play Rendered Video & Inspect Manifest
- **Action:** Click **"Play Rendered Video"** in the browser, then click **"View Manifest"**.
- **Speaking Points:**
  - *"The rendered video plays back smoothly with synchronized audio."*
  - *"The output `manifest.json` provides complete cryptographic auditability: source SHA-256, output timeline hash, FFprobe stream sync validation confirming 0 frames of A/V offset, and rights confirmation."*

### 7:00 – 7:45 | 9. Code Architecture & Test Verification
- **Action:** Switch to terminal and run:
  ```bash
  python -m pytest -q
  ```
  Then quickly show `app/timeline.py` in VS Code.
- **Speaking Points:**
  - *"Running pytest: all 110 automated tests pass cleanly in 10 seconds."*
  - *"In `app/timeline.py`, notice how our timeline data model uses immutable `SourceInterval` segments and word-ID dictionaries."*
  - *"The parser converts natural language to structured operations, but ordinary deterministic Python code executes the timeline math. An LLM never directly mutates timeline state."*

### 7:45 – 8:00 | 10. Conclusion
- **Speaking Points:**
  - *"IncuEdit proves that prompt-based editing can be fast, 100% deterministic, and rock-solid. All source code, tests, and documentation are available in the repository at https://github.com/rvsr26/incubrix. Thank you!"*
