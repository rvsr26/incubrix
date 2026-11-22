# Sources and third-party components

Candidate: **Rajala Vishnu Sathwick Reddy** (`rajalavishnureddy@gmail.com`)  
Assessment: **IncuBrix Software Engineer Assessment — Problem Statement 2 (PS2): IncuEdit**  
Date: **November 2026**

## Third-Party Components & Commercial-Use Licences

| Component | Version | Role | Declared Licence | Commercial Use Notes |
|---|---|---|---|---|
| **Python** | 3.14.4 (Windows x64) / 3.12+ | Runtime environment | Python Software Foundation License (PSFL) | Fully permissive for commercial software |
| **FastAPI** | 0.128.2+ | HTTP API web framework | MIT | Fully permissive |
| **Starlette** | 0.50.0+ | ASGI toolkit | BSD-3-Clause | Fully permissive |
| **Uvicorn** | 0.48.0+ | ASGI server | BSD-3-Clause | Fully permissive |
| **Pydantic** | 2.13.5+ | Data validation & settings | MIT | Fully permissive |
| **python-multipart** | 0.0.29+ | Streaming multipart form parsing | Apache-2.0 | Fully permissive |
| **HTTPX** | 0.28.1+ | HTTP client & TestClient | BSD-3-Clause | Fully permissive |
| **PyYAML** | 6.0.3+ | YAML session definition parser | MIT | Fully permissive |
| **boto3** | 1.43.18+ (optional) | AWS S3 / MinIO client | Apache-2.0 | Fully permissive |
| **pytest** | 9.0.2+ | Test automation suite | MIT | Developer dependency |
| **openpyxl** | 3.1.5+ | Excel report processing | MIT | Developer dependency |
| **static-ffmpeg / FFmpeg** | 8.0.1 (Gyan static build) | Media probing & deterministic rendering | LGPL v2.1+ / GPL | Permissive for media encoding CLI invocation |
| **React** | 18.3.1 | Frontend component library | MIT | Fully permissive |
| **React-DOM** | 18.3.1 | React DOM renderer | MIT | Fully permissive |
| **TypeScript** | 5.4.5 | Frontend type safety | Apache-2.0 | Fully permissive |
| **Vite** | 5.2.11 | Frontend bundler | MIT | Fully permissive |
| **Lucide React** | 0.383.0 | Modern UI icon set | ISC | Fully permissive |
| **MinIO** | Docker profile (optional) | S3-compatible local object storage | AGPLv3 | Local dev profile only; separate network process |
| **faster-whisper** | Optional plugin | Optional local speech transcription | MIT | Optional plugin path; zero keys needed in default path |
| **pyannote.audio** | Optional plugin | Optional speaker diarization | MIT / Non-commercial weights | Optional interface; weights require Hugging Face commercial licensing |

*Note on styling:* The React frontend studio is styled using clean, standard dark theme CSS (`index.css`) with custom component styling and Lucide icons. Tailwind CSS is not included in the dependency tree.

## Verification Environment

- **Host Machine:** Windows 11 x64, Intel Core i7, 16 GB RAM
- **Python Version:** 3.14.4 (win32/amd64)
- **FFmpeg & FFprobe Version:** 8.0.1-full_build-www.gyan.dev (configured with automatic binary fallback in `app/config.py`)
- **Node.js & npm:** Node.js v20.18.0, npm 10.8.2
- **Test Results:** 110 automated tests passing in 16.28 seconds (`pytest -q`)
- **Batch Verification:** 20/20 test sessions passing with 100% determinism across 3 independent rounds (60/60 runs bitwise identical)
- **Docker Compose Status:** `docker compose config` syntax validated; runtime container execution unverified due to Docker Desktop daemon being stopped on Windows host

## Media & Data Provenance

1. `examples/demo_media.mp4`: A synthetic 16-second test pattern with a generated sine tone created using FFmpeg `testsrc2` and `sine` sources. 100% rights-clean and copyright-free.
2. `examples/sample_transcript.json`: Synthetic word-level transcript fixture with 2 speaker labels (`host`, `guest`), word boundaries, and confidence metrics.
3. No copyrighted audio, music, video, or biometric personal data is bundled or required.
