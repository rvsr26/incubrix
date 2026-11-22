# IncuBrix Assessment — IncuEdit: Prompt-Based Video Editing Engine (PS2)

**Candidate:** Rajala Vishnu Sathwick Reddy (`rajalavishnureddy@gmail.com`)  
**College:** Amrita Vishwa Vidyapeetham, Coimbatore (B.Tech CSE, Class of 2027)  
**Repository:** [https://github.com/rvsr26/incubrix](https://github.com/rvsr26/incubrix)  
**Workbook:** `Assessment2_Rajala_Vishnu_Sathwick_Reddy.xlsx`

---

## Overview

**IncuEdit** is a deterministic, prompt-driven video editing engine built for the IncuBrix Software Engineer Assessment (Problem Statement 2).

It translates natural language editing instructions ("cut first 3 seconds", "remove filler words", "bleep secret", "speed up section 2 by 1.5x") into an immutable source-media timeline model, guaranteeing:
- **Zero Loss / Immutability**: Original source media is never modified.
- **Content-Anchored Effects**: Captions, mutes, and bleeps anchor to source word IDs rather than floating clock positions.
- **100% Determinism**: 20/20 test sessions produce bitwise-identical timeline states across 3 independent rounds (60 executions).
- **Exact A/V Synchronization**: 0 frames offset across verified renders.
- **Zero Cloud Spend**: $0 external API cost in default execution mode (mock/offline adapters provided).

---

## Directory Structure

```
incubrix/
├── Assessment2_Rajala_Vishnu_Sathwick_Reddy.xlsx   # Official candidate submission workbook
├── PROJECT_AUDIT.md                                # Comprehensive audit of requirements & status
├── IncuBrix_Assessment_*.pdf                       # Assessment problem statements & briefs
├── incuedit/                                       # Core application source
│   ├── app/                                        # FastAPI backend, timeline engine & renderers
│   │   ├── engine.py                               # Editing engine & instruction dispatch
│   │   ├── timeline.py                             # Immutable timeline data model
│   │   ├── parser.py                               # Deterministic & LLM instruction parsing
│   │   ├── render.py                               # FFmpeg render orchestrator
│   │   ├── transcription.py                        # Faster-Whisper & Diarization provider interface
│   │   ├── otio_export.py                          # OpenTimelineIO interchange serializer
│   │   ├── config.py                               # Production-hardened environment config
│   │   └── main.py                                 # FastAPI REST API & job manager
│   ├── frontend/                                   # React 18 + TypeScript + Vite video studio UI
│   │   ├── src/App.tsx                             # Interactive editing studio & timeline scrubber
│   │   └── dist/                                   # Precompiled standalone distribution
│   ├── tests/                                      # 110-test verification suite
│   │   ├── test_timeline.py                        # Non-destructive edit & anchoring tests
│   │   ├── test_engine.py                          # Instruction application tests
│   │   ├── test_api.py                             # REST API & webhook tests
│   │   ├── test_scenarios_40.py                    # 40 edge-case editing scenarios
│   │   ├── test_security.py                        # Webhook secret validation & HMAC-SHA256 tests
│   │   └── test_speaker_diarization.py             # Diarization & unknown speaker safety tests
│   ├── scripts/                                    # Automation & verification scripts
│   │   ├── verify_determinism.py                   # 3-round bitwise determinism verifier
│   │   ├── validate_contract.py                    # OpenAPI route parity validator
│   │   ├── session_runner.py                       # Batch YAML session runner
│   │   └── package_and_verify.py                   # Clean-extraction packaging & verification
│   ├── artifacts/                                  # Reproducible verification artifacts
│   │   ├── determinism_final/                      # 3-round hash outputs & report.json
│   │   └── session_pack/                           # Rendered MP4s & sync manifests
│   ├── openapi.yaml                                # Complete OpenAPI 3.1 contract
│   ├── docker-compose.yml                          # Multi-container deployment definition
│   ├── Dockerfile                                  # Container image build file
│   ├── README.md                                   # Detailed application documentation
│   ├── REPORT.md                                   # Comprehensive implementation & metric report
│   ├── SOURCES.md                                  # Third-party libraries & licenses
│   └── AI_USE.md                                   # Tool disclosure & AI assistance record
└── .gitignore
```

---

## Quick Start

### 1. Backend Setup & Run

```bash
cd incuedit
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Dark Studio UI:** [http://localhost:8000](http://localhost:8000)
- **React Studio UI:** [http://localhost:8000/app/](http://localhost:8000/app/)

### 2. Run Test Suite (110 Tests)

```bash
cd incuedit
python -m pytest -q
```
*Expected: 110 passed, 0 failed.*

### 3. Run Determinism Verification (3 Rounds, 60 Executions)

```bash
cd incuedit
python scripts/verify_determinism.py
```
*Expected: 20/20 sessions deterministic (100.0%).*

### 4. Validate OpenAPI Contract Parity

```bash
cd incuedit
python scripts/validate_contract.py
```
*Expected: 23/23 routes matched, passed: true.*

### 5. Frontend Development & Build

```bash
cd incuedit/frontend
npm install
npm run build
```
*Build output is bundled to `incuedit/frontend/dist` and served directly by FastAPI.*

---

## Key Verification Results

| Metric | Target / Claim | Verified Result | Evidence Path |
|---|---|---|---|
| **Test Suite** | Comprehensive coverage | **110/110 passing** | `incuedit/tests/` |
| **OpenAPI Contract** | 100% route alignment | **23/23 routes matched** | `incuedit/scripts/validate_contract.py` |
| **Timeline Determinism** | 100% reproducible | **20/20 sessions, 60 runs bitwise match** | `incuedit/artifacts/determinism_final/report.json` |
| **A/V Sync Offset** | Zero lip-sync drift | **0.0 frames offset** | `incuedit/artifacts/session_pack/*_manifest.json` |
| **Instruction Latency** | Sub-second | **3.5 ms median, 9.0 ms max** | `incuedit/artifacts/session_pack/results.json` |
| **External API Cost** | Zero cost default | **$0.00** | Offline mock adapters |
| **Declaration Status** | Candidate signature | **Preserved blank for personal review** | Sheet `7_Declaration` B4:B13 |

---

## Contact & Review

- **Candidate:** Rajala Vishnu Sathwick Reddy
- **Email:** [rajalavishnureddy@gmail.com](mailto:rajalavishnureddy@gmail.com)
- **Review Access:** Reviewers from IncuBrix (`techteam@incubrix.com`) may request collaborator access to this repository.
