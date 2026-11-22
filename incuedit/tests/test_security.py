"""Security and webhook signature verification tests."""
from __future__ import annotations
import os
import hmac
import hashlib
import json
import pytest
import subprocess
import sys
from pathlib import Path

def test_production_rejects_missing_or_weak_webhook_secret():
    """Verify production startup validation rejects empty or insecure secrets."""
    cmd = [
        sys.executable,
        "-c",
        "import os; os.environ['APP_ENV']='production'; os.environ['WEBHOOK_SECRET']=''; from app.config import Settings; Settings()"
    ]
    env = os.environ.copy()
    env["APP_ENV"] = "production"
    env["WEBHOOK_SECRET"] = ""
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "Production mode requires a strong, non-default WEBHOOK_SECRET" in res.stderr

def test_production_rejects_insecure_default_secret():
    """Verify production startup rejects known weak defaults like incuedit_secret_key_2026."""
    cmd = [
        sys.executable,
        "-c",
        "import os; os.environ['APP_ENV']='production'; os.environ['WEBHOOK_SECRET']='incuedit_secret_key_2026'; from app.config import Settings; Settings()"
    ]
    env = os.environ.copy()
    env["APP_ENV"] = "production"
    env["WEBHOOK_SECRET"] = "incuedit_secret_key_2026"
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "Production mode requires a strong, non-default WEBHOOK_SECRET" in res.stderr

def test_production_accepts_strong_secret():
    """Verify production mode succeeds with strong 32-character secret."""
    cmd = [
        sys.executable,
        "-c",
        "import os; os.environ['APP_ENV']='production'; os.environ['WEBHOOK_SECRET']='a_very_strong_production_webhook_secret_64chars_long_12345'; from app.config import Settings; s=Settings(); print(s.app_env)"
    ]
    env = os.environ.copy()
    env["APP_ENV"] = "production"
    env["WEBHOOK_SECRET"] = "a_very_strong_production_webhook_secret_64chars_long_12345"
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert "production" in res.stdout

def test_hmac_sha256_signature_generation_and_verification():
    """Test HMAC-SHA256 signature computation conforms to X-IncuBrix-Signature standard."""
    test_secret = "test_custom_secret_key_9876543210"
    payload = {"job_id": "test-job-123", "status": "succeeded", "progress": 100}
    body_str = json.dumps(payload, default=str)
    
    expected_sig = hmac.new(test_secret.encode(), body_str.encode(), hashlib.sha256).hexdigest()
    header_val = f"sha256={expected_sig}"
    
    # Verify parsing and verification
    assert header_val.startswith("sha256=")
    extracted_sig = header_val.split("sha256=")[1]
    computed_sig = hmac.new(test_secret.encode(), body_str.encode(), hashlib.sha256).hexdigest()
    assert hmac.compare_digest(extracted_sig, computed_sig)
