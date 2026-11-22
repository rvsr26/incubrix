from __future__ import annotations
import os
import shutil
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env if present
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# Automatically register static-ffmpeg if system ffmpeg is missing
if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except Exception:
        pass

import secrets
import logging

_logger = logging.getLogger("incuedit.config")

# Webhook secret initialization with production enforcement
_raw_webhook_secret = os.getenv("WEBHOOK_SECRET")
_app_env = os.getenv("APP_ENV", "development").strip().lower()

_INSECURE_SECRETS = {
    "incuedit_secret_key_2026",
    "secret",
    "password",
    "changeme",
    "admin",
    "123456",
    "default",
}

def _is_insecure_or_placeholder(val: str | None) -> bool:
    if not val:
        return True
    s = val.strip().lower()
    if s in _INSECURE_SECRETS:
        return True
    if "replace_me" in s or s.startswith("your_") or "placeholder" in s:
        return True
    if len(s) < 16:
        return True
    return False

if _app_env == "production":
    if _is_insecure_or_placeholder(_raw_webhook_secret):
        raise ValueError("Production mode requires a strong, non-default WEBHOOK_SECRET (minimum 16 characters).")
    _active_webhook_secret = _raw_webhook_secret.strip()
else:
    if not _is_insecure_or_placeholder(_raw_webhook_secret):
        _active_webhook_secret = _raw_webhook_secret.strip()
    else:
        # Cryptographically secure ephemeral random secret for local development / test
        _active_webhook_secret = secrets.token_hex(32)
        _logger.info("Generated ephemeral cryptographically secure secret for non-production environment.")

@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "IncuEdit")
    app_env: str = os.getenv("APP_ENV", "development")
    data_dir: Path = Path(os.getenv("DATA_DIR", "./data"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "500"))
    transcription_provider: str = os.getenv("TRANSCRIPTION_PROVIDER", "mock")
    diarization_provider: str = os.getenv("DIARIZATION_PROVIDER", "none")
    ffmpeg_bin: str = os.getenv("FFMPEG_BIN", "ffmpeg")
    ffprobe_bin: str = os.getenv("FFPROBE_BIN", "ffprobe")
    time_policy: str = os.getenv("TIME_POLICY", "current_timeline")
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    cost_estimate_usd_per_video_minute: float = float(os.getenv("COST_ESTIMATE_USD_PER_VIDEO_MINUTE", "0"))
    webhook_secret: str = _active_webhook_secret

settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
(settings.data_dir / "videos").mkdir(exist_ok=True)
(settings.data_dir / "renders").mkdir(exist_ok=True)
