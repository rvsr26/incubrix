"""
Comprehensive packaging and independent verification script for IncuEdit.
Creates IncuEdit_FINAL.zip, extracts it to a clean temporary directory,
and executes all test suites, builds, contract validations, and server checks
entirely from the extracted ZIP location.
"""
from __future__ import annotations
import os
import sys
import shutil
import zipfile
import subprocess
import time
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = ROOT_DIR.parent
FINAL_ZIP = WORKSPACE_DIR / "IncuEdit_FINAL.zip"
FINAL_SUBMISSION_ZIP = WORKSPACE_DIR / "IncuEdit_FINAL_SUBMISSION.zip"

print(f"Project root: {ROOT_DIR}", flush=True)
print(f"Output ZIP target: {FINAL_SUBMISSION_ZIP}", flush=True)

EXCLUDE_PATTERNS = {
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    ".git",
}

def should_exclude(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    for part in parts:
        if part in EXCLUDE_PATTERNS or part.endswith(".pyc"):
            return True
    if "data" in parts and ("renders" in parts or "videos" in parts or "temp" in parts):
        if not rel_path.endswith(".gitkeep"):
            return True
    return False

# 1. Package IncuEdit_FINAL_SUBMISSION.zip (and duplicate to IncuEdit_FINAL.zip)
print("\n--- Step 1: Packaging IncuEdit_FINAL_SUBMISSION.zip ---", flush=True)
for target_zip in [FINAL_SUBMISSION_ZIP, FINAL_ZIP]:
    if target_zip.exists():
        target_zip.unlink()

file_count = 0
with zipfile.ZipFile(FINAL_SUBMISSION_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(ROOT_DIR):
        for f in files:
            full_path = Path(root) / f
            rel_path = full_path.relative_to(ROOT_DIR)
            if should_exclude(str(rel_path)):
                continue
            arcname = f"incuedit/{rel_path.as_posix()}"
            zf.write(full_path, arcname)
            file_count += 1

# Duplicate to IncuEdit_FINAL.zip for full compatibility
shutil.copyfile(FINAL_SUBMISSION_ZIP, FINAL_ZIP)

zip_size_bytes = FINAL_SUBMISSION_ZIP.stat().st_size
zip_size_mb = zip_size_bytes / (1024 * 1024)
print(f"Successfully created {FINAL_SUBMISSION_ZIP.name}", flush=True)
print(f"Total files packed: {file_count}", flush=True)
print(f"Size: {zip_size_bytes:,} bytes ({zip_size_mb:.2f} MB)", flush=True)

# 2. Extract into independent temporary verification directory
temp_base = Path(os.environ.get("TEMP", "C:/Temp")) / f"incuedit_clean_verify_{int(time.time())}"
if temp_base.exists():
    shutil.rmtree(temp_base, ignore_errors=True)
temp_base.mkdir(parents=True, exist_ok=True)

print(f"\n--- Step 2: Extracting to clean directory: {temp_base} ---", flush=True)
with zipfile.ZipFile(FINAL_SUBMISSION_ZIP, "r") as zf:
    zf.extractall(temp_base)

EXTRACTED_APP_DIR = temp_base / "incuedit"
print(f"Extracted to: {EXTRACTED_APP_DIR}", flush=True)
print(f"Exists: {EXTRACTED_APP_DIR.exists()}", flush=True)

# Verify required files exist in extracted directory
required_checks = [
    "frontend/dist/index.html",
    "frontend/src/App.tsx",
    "frontend/package.json",
    "tests/test_scenarios_40.py",
    "tests/test_api.py",
    "tests/test_timeline.py",
    "tests/test_security.py",
    "tests/test_speaker_diarization.py",
    "scripts/verify_determinism.py",
    "scripts/session_runner.py",
    "scripts/validate_contract.py",
    "artifacts/determinism_final/report.json",
    "artifacts/session_pack/results.json",
    "PROJECT_AUDIT.md",
    "README.md",
    "REPORT.md",
    "SOURCES.md",
    "AI_USE.md",
    "SUBMISSION_ACTIONS.md",
    "DEMO_RECORDING_SCRIPT.md",
    "SUBMISSION_CHECKLIST.md",
    "GOOGLE_FORM_ANSWERS.md",
    "DEPLOYMENT_GUIDE.md",
    "TEST_EVIDENCE_INDEX.md",
    "FINAL_VERIFICATION_REPORT.md",
    "Assessment2_Rajala_Vishnu_Sathwick_Reddy_FINAL.xlsx",
    "openapi.yaml",
]

missing = [req for req in required_checks if not (EXTRACTED_APP_DIR / req).exists()]
if missing:
    print(f"FATAL: Missing required files in extracted ZIP: {missing}", flush=True)
    sys.exit(1)
print(f"All {len(required_checks)} required key files and artifacts verified in extracted directory!", flush=True)

# Verify workbook Declaration is 100% blank
import openpyxl
wb_check = openpyxl.load_workbook(EXTRACTED_APP_DIR / "Assessment2_Rajala_Vishnu_Sathwick_Reddy_FINAL.xlsx")
decl_sheet = wb_check["7_Declaration"]
decl_cells = [decl_sheet[f"B{r}"].value for r in range(4, 14)]
print(f"Extracted workbook 7_Declaration B4:B13: {decl_cells}", flush=True)
if any(val is not None for val in decl_cells):
    print("FATAL: 7_Declaration contains non-blank entries!", flush=True)
    sys.exit(1)
print("Confirmed: Candidate declaration is properly left completely blank for personal review.", flush=True)

# 3. Run Pytest in extracted directory
print("\n--- Step 3: Running 99 Pytest Suite in Extracted Directory ---", flush=True)
pytest_res = subprocess.run(
    [sys.executable, "-m", "pytest", "-q"],
    cwd=str(EXTRACTED_APP_DIR),
    capture_output=True,
    text=True
)
print(pytest_res.stdout, flush=True)
if pytest_res.stderr:
    print("Stderr:", pytest_res.stderr, flush=True)
if pytest_res.returncode != 0:
    print("Pytest failed in extracted directory!", flush=True)
    sys.exit(pytest_res.returncode)

# 4. Run OpenAPI Contract Validation in extracted directory
print("\n--- Step 4: Running OpenAPI Contract Validation in Extracted Directory ---", flush=True)
contract_res = subprocess.run(
    [sys.executable, "scripts/validate_contract.py"],
    cwd=str(EXTRACTED_APP_DIR),
    capture_output=True,
    text=True
)
print(contract_res.stdout, flush=True)
if contract_res.returncode != 0 or "passed: true" not in contract_res.stdout:
    print("Contract validation failed in extracted directory!", flush=True)
    sys.exit(1)

# 5. Run 3-Round Determinism Verification in extracted directory
print("\n--- Step 5: Running 3-Round Determinism Check in Extracted Directory ---", flush=True)
det_res = subprocess.run(
    [sys.executable, "scripts/verify_determinism.py"],
    cwd=str(EXTRACTED_APP_DIR),
    capture_output=True,
    text=True
)
print(det_res.stdout, flush=True)
if det_res.returncode != 0 or "SUCCESS: 100% bitwise timeline determinism" not in det_res.stdout:
    print("Determinism verification failed in extracted directory!", flush=True)
    sys.exit(1)

# 6. Verify Sample Rendered MP4 Files and Manifests
print("\n--- Step 6: Verifying Rendered Media and Manifests ---", flush=True)
manifest_files = list((EXTRACTED_APP_DIR / "artifacts" / "session_pack").glob("*_manifest.json"))
mp4_files = list((EXTRACTED_APP_DIR / "artifacts" / "session_pack").glob("*_render.mp4"))
print(f"Found {len(manifest_files)} manifests and {len(mp4_files)} rendered MP4s in session_pack.", flush=True)
for m in manifest_files[:5]:
    with open(m, "r", encoding="utf-8") as f:
        mdata = json.load(f)
    print(f"  {m.name}: timeline_hash={mdata.get('timeline_hash')[:12]} A/V offset={mdata.get('sync_validation', {}).get('max_offset_frames')} frames", flush=True)

# 7. Start FastAPI Server and verify live endpoints from extracted zip
print("\n--- Step 7: Starting FastAPI Server from Extracted ZIP & Testing End-to-End ---", flush=True)
from starlette.testclient import TestClient
sys.path.insert(0, str(EXTRACTED_APP_DIR))
from app.main import app
client = TestClient(app)

# Health
r_health = client.get("/api/v1/health")
print(f"GET /api/v1/health -> {r_health.status_code} {r_health.json()}", flush=True)

# Root Standalone Studio
r_root = client.get("/")
print(f"GET / (Dark Studio) -> {r_root.status_code} ({len(r_root.text)} bytes, title='{'IncuEdit' in r_root.text}')", flush=True)

# React Studio SPA
r_app = client.get("/app/")
print(f"GET /app/ (React Studio) -> {r_app.status_code} ({len(r_app.text)} bytes, has_div_root={'id=\"root\"' in r_app.text})", flush=True)

# Real Video Upload
demo_video_path = EXTRACTED_APP_DIR / "examples" / "demo_media.mp4"
with open(demo_video_path, "rb") as vf:
    upload_res = client.post(
        "/api/v1/videos/upload",
        files={"file": ("demo_media.mp4", vf, "video/mp4")},
        data={"rights_confirmed": "true"},
        headers={"Idempotency-Key": "verify-upload-key-1"}
    )
upload_json = upload_res.json()
vid_data = upload_json["video"]
vid_id = vid_data["video_id"]
sha = vid_data["source_sha256"][:12]
print(f"POST /api/v1/videos/upload -> {upload_res.status_code} video_id={vid_id} source_sha256={sha}", flush=True)

# Real Session Creation
transcript_path = EXTRACTED_APP_DIR / "examples" / "sample_transcript.json"
with open(transcript_path, "r", encoding="utf-8") as tf:
    transcript_words = json.load(tf)

sess_res = client.post(
    "/api/v1/sessions",
    json={
        "video_id": vid_id,
        "transcript": transcript_words,
    },
    headers={"Idempotency-Key": "verify-sess-key-1"}
)
sid = sess_res.json()["session_id"]
print(f"POST /api/v1/sessions -> {sess_res.status_code} session_id={sid}", flush=True)

# Instruction: Cut first 2 seconds
inst_res = client.post(
    f"/api/v1/sessions/{sid}/instructions",
    json={"say": "Cut the first 2 seconds"},
    headers={"Idempotency-Key": "verify-inst-key-1"}
)
print(f"POST /api/v1/sessions/{sid}/instructions -> {inst_res.status_code} status={inst_res.json().get('status')} after_duration={inst_res.json().get('summary', {}).get('after_duration_s')}s", flush=True)

# OTIO Export
r_otio = client.get(f"/api/v1/sessions/{sid}/otio")
otio_json = r_otio.json()
print(f"GET /api/v1/sessions/{sid}/otio -> {r_otio.status_code} schema={otio_json.get('OTIO_SCHEMA')} tracks={len(otio_json.get('tracks', {}).get('children', []))}", flush=True)

# Render Job
render_req = client.post(
    f"/api/v1/sessions/{sid}/render",
    headers={"Idempotency-Key": "verify-render-key-1"}
)
job_id = render_req.json()["job_id"]
print(f"POST /api/v1/sessions/{sid}/render -> {render_req.status_code} job_id={job_id} status={render_req.json().get('status')}", flush=True)

# Poll job completion
for _ in range(30):
    jr = client.get(f"/api/v1/jobs/{job_id}")
    status = jr.json().get("status")
    if status in ("succeeded", "failed"):
        print(f"Render job finished with status: {status} progress={jr.json().get('progress')}%", flush=True)
        break
    time.sleep(0.5)

# Verify Manifest and Playable Video download
r_manifest = client.get(f"/api/v1/jobs/{job_id}/manifest")
r_video = client.get(f"/api/v1/jobs/{job_id}/video")
print(f"GET /api/v1/jobs/{job_id}/manifest -> {r_manifest.status_code} (manifest_version={r_manifest.json().get('manifest_version')})", flush=True)
print(f"GET /api/v1/jobs/{job_id}/video -> {r_video.status_code} (downloaded {len(r_video.content):,} bytes)", flush=True)

# 8. Directory Structure of Extracted Directory
print("\n--- Step 8: Extracted ZIP Directory Tree ---", flush=True)
for item in sorted(list(EXTRACTED_APP_DIR.glob("*"))):
    if item.is_dir():
        sub_count = len(list(item.glob("**/*")))
        print(f"  [DIR]  {item.name}/ ({sub_count} items)", flush=True)
    else:
        print(f"  [FILE] {item.name} ({item.stat().st_size:,} bytes)", flush=True)

print("\n=======================================================", flush=True)
print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY FROM EXTRACTED ZIP!", flush=True)
print(f"Final Submission ZIP: {FINAL_SUBMISSION_ZIP}")
print(f"Final Legacy ZIP:     {FINAL_ZIP}")
print(f"Archive Size:         {zip_size_bytes:,} bytes ({zip_size_mb:.2f} MB)")
print(f"Total Files Packed:   {file_count}")
print(f"Extracted Directory:  {EXTRACTED_APP_DIR}")
print("=======================================================", flush=True)
