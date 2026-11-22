# AI tool usage disclosure

Candidate: **Rajala Vishnu Sathwick Reddy** (`rajalavishnureddy@gmail.com`)  
Assessment: **IncuBrix Software Engineer Assessment — Problem Statement 2 (PS2): IncuEdit**  
Date: **November 2026**

## Tools and Models Used

1. **ChatGPT (GPT-4 / GPT-6, OpenAI)**
   - **Purpose:** Initial architectural planning, preliminary scaffold code, initial test fixtures, initial OpenAPI schema drafting, and base session definition.
   - **Date:** Initial repository preparation (November 2026).

2. **Google Antigravity (Google DeepMind)**
   - **Purpose:** Full repository audit, deep implementation of core timeline engine, OpenTimelineIO (OTIO) export format serializer, caption color and font sizing, speaker-specific and relative cut parsing, 42 hard-case automated scenarios (`tests/test_scenarios_40.py`), static FFmpeg/FFprobe tooling integration, React 18 + TypeScript + Vite studio frontend SPA compilation, FastAPI routes (`/otio`, `/history`, `/undo`, `/redo`), secure environment-based webhook secrets and HMAC-SHA256 signature verification, speaker diarization adapter architecture, 3-round determinism verification (60/60 runs bitwise identical), and comprehensive workbook completion.
   - **Date:** November 2026.

## Runtime Architecture & Zero-Key Path

- At runtime, the core editing pipeline is **100% deterministic, ordinary Python code**. No external LLM or cloud API is queried during timeline manipulation, session runs, or video export.
- Zero API keys are required to execute all 110 automated tests, run the 20 batch sessions, or operate the web studio.
- The candidate understands every component, architecture rule, data model, and algorithm in this codebase and is prepared to explain and modify any part during the live assessment interview.
