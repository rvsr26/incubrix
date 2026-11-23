# IncuBrix Assessment 2 — Google Form Submission Answers

**Candidate:** RAJALA VISHNU SATHWICK REDDY  
**Email:** `rajalavishnureddy@gmail.com`  
**Phone:** 9390934449  
**College:** Amrita Vishwa Vidyapeetham, Coimbatore  
**Degree:** B.Tech, Computer Science and Engineering (Class of 2027)  
**Problem Statement:** PS2 — Prompt-Based Video Editing Engine (IncuEdit)  
**Submission Deadline:** 23 November 2026, 11:59 PM IST  

---

> [!IMPORTANT]
> **Instructions for the Candidate:**  
> This document maps every expected field in the IncuBrix Assessment 2 Google Form to a verified, defensible answer.  
> Each field is marked with one of four tags:
> - `[VERIFIED AND READY TO COPY-PASTE]` — Fully verified from the project code and tests. Safe to copy directly.
> - `[REQUIRES YOUR PERSONAL INFORMATION]` — You must enter your personal university details (e.g. registration ID).
> - `[REQUIRES YOUR PUBLIC LINK OR ACCOUNT ACTION]` — You must paste your uploaded video link or confirm collaborator access.
> - `[REQUIRES YOUR PERSONAL DECLARATION AND AGREEMENT]` — You must personally confirm and agree; never automated.

---

## Section 1: Candidate Information

### 1. Amrita Registration ID / Roll Number
- **Status:** `[REQUIRES YOUR PERSONAL INFORMATION]`
- **Answer:**
```
[ENTER YOUR OFFICIAL AMRITA REGISTRATION ID, e.g., CB.EN.U4CSE23XXX]
```

### 2. Full Name
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
RAJALA VISHNU SATHWICK REDDY
```

### 3. Registered Email Address
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
rajalavishnureddy@gmail.com
```

### 4. Phone Number
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
9390934449
```

### 5. College & Degree
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
Amrita Vishwa Vidyapeetham, Coimbatore — B.Tech, Computer Science and Engineering
```

### 6. Graduation Year
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
2027
```

### 7. Application Track
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
Software Engineer
```

### 8. Problem Statement
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
PS2 — Prompt-Based Video Editing Engine
```

---

## Section 2: Repository & Deliverables

### 9. Completed Submission Form (Excel)
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Action:** Attach the file:
```
Assessment2_Rajala_Vishnu_Sathwick_Reddy_FINAL.xlsx
```
*(Ensure you have personally completed Sheet 7_Declaration before uploading!)*

### 10. GitHub Repository URL
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
https://github.com/rvsr26/incubrix
```

### 11. Repository Access Confirmation
- **Status:** `[REQUIRES YOUR PUBLIC LINK OR ACCOUNT ACTION]`
- **Answer:**
```
Private repository. Reviewers from IncuBrix (techteam@incubrix.com) are granted collaborator access. If additional access is required, please contact rajalavishnureddy@gmail.com.
```
*(Make sure to go to https://github.com/rvsr26/incubrix/settings/access and invite techteam@incubrix.com)*

### 12. Live Demo URL
- **Status:** `[REQUIRES YOUR PUBLIC LINK OR ACCOUNT ACTION]`
- **Answer:**
```
Local Studio: http://localhost:8000/app (React 18 Studio) and http://localhost:8000 (Dark Studio).
Public Cloud Deployment: [IF DEPLOYED, PASTE YOUR PUBLIC URL HERE, e.g., https://incuedit.onrender.com; IF NOT DEPLOYED, ENTER: "Local deployment verified. Cloud deployment steps documented in DEPLOYMENT_GUIDE.md"]
```

### 13. Live Demo Access Token or Login Instructions
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
No login or authentication token required. The local studio runs openly on port 8000.
```

### 14. Demo Video URL (Max 8 minutes, unedited)
- **Status:** `[REQUIRES YOUR PUBLIC LINK OR ACCOUNT ACTION]`
- **Answer:**
```
[ENTER YOUR UNEDITED DEMO VIDEO URL — e.g. YouTube Unlisted link or Google Drive viewable link]
```
*(Follow the step-by-step recording plan in DEMO_RECORDING_SCRIPT.md)*

---

## Section 3: Assessment Claims & Self-Score

### 15. Do all Must-haves pass?
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Recommended Selection:**
```
No / 7 of 8 Met (Honest assessment: Must-haves 1 through 7 are fully implemented and verified with 110 automated tests, 0-frame A/V sync, and 100% determinism. Must-have 8 is Partial because local execution is verified, but public cloud deployment and Docker host daemon were not executed on this machine.)
```

### 16. Highest Level Completed
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Recommended Selection:**
```
Core (with Advanced and Outstanding features implemented: 40+ scenario tests, OpenTimelineIO export, silence snapping, low-confidence word flagging, and non-destructive DAG history. 60-minute scale and real GPU diarization marked No/Partial for strict honesty.)
```

### 17. Self-Assessed Score
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Defensible Score:**
```
33 / 60 on automated screening items (18/20 Integration + 15/40 Core Level marks claimed).
Overall self-score estimate: 60 / 100 (accounting for verified must-haves, 110 automated tests, OpenAPI contract parity, 100% determinism, and zero-frame render sync, while honestly deducting for unverified 60m scale, public cloud hosting, and Docker daemon runtime).
```

### 18. Outcome Summary (Concise Engineering Overview)
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
IncuEdit is a fully deterministic, prompt-driven video editing engine with an immutable source-media model:
1. Non-Destructive Editing: The original video source SHA-256 is immutable. Every edit produces a versioned timeline state without re-encoding until final export.
2. Word-Anchored Effects: Captions, mutes, bleeps, and speed changes anchor to stable word IDs, preserving exact placement across cuts, reorders, and undo/redo operations.
3. Determinism: 20/20 YAML scripted sessions verified 100% bitwise deterministic across 3 consecutive rounds (60 executions, 0 hash mismatches).
4. Render Accuracy: Frame-accurate FFmpeg pipeline verified with 0 frames A/V offset and 0 frames timeline duration error across 5 verified render manifests.
5. Latency: Median instruction latency is 3.5 ms (slowest 9.0 ms) across 38 operations on 16-second video fixtures.
6. Interchange: Exports timeline state to OpenTimelineIO (OTIO 1.0 schema) with audio/video track layout.
7. Verification: 110 automated tests passing, 23/23 OpenAPI contract routes matched, and clean React 18 studio SPA with timeline scrubbing.
```

### 19. Known Limitations
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
1. Scale: Evaluated on short video fixtures (16 seconds); 60-minute full-length processing was not measured due to local hardware constraints.
2. Diarization: Implemented via a clean provider interface with unknown-speaker fallbacks and clarification safety rules; real pyannote diarization requires external Hugging Face tokens and GPU acceleration.
3. Docker Runtime: docker-compose.yml syntax is 100% verified, but the Docker Desktop daemon was not running on the candidate's Windows host; local Python and Vite run natively.
4. Word Clipping Metric: Tested with synthetic tone fixtures and 80ms silence snapping padding; human acoustic panel evaluation was not conducted.
```

### 20. AI Tools, Models, APIs, Paid Services, and Total Cost
- **Status:** `[VERIFIED AND READY TO COPY-PASTE]`
- **Answer:**
```
- AI Coding Tools: ChatGPT (architecture design, instruction parsing strategies, and code review) and Google Antigravity (code implementation, refactoring, test execution, and packaging).
- Models/APIs: Local deterministic parser and mock transcription adapter used in default path.
- Paid External Services: None ($0.00 spend).
- Total External Cost: USD $0.00.
```

---

## Section 4: Personal Candidate Declaration

### 21. Candidate Declaration Confirmation
- **Status:** `[REQUIRES YOUR PERSONAL DECLARATION AND AGREEMENT]`
- **Action Required:**
```
You must personally review and check each declaration statement in the Google Form and in Sheet 7_Declaration of the workbook:
- Individual work that you can explain and defend.
- All claims backed by real linked evidence.
- Full disclosure of AI tools in AI_USE.md and SOURCES.md.
- Commercial licensing compliance in default path.
- No hand-edited outputs presented as automated.
- Consent and privacy compliance.
- Zero secrets or API keys committed.
- Sign your full name and the current date.
```
