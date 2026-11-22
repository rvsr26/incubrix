from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
from app.config import settings
from app.errors import EngineError

VIDEO_EXTS = {".mp4", ".mov", ".m4v"}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def probe_video(path: Path) -> dict:
    cmd = [settings.ffprobe_bin, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    try:
        raw = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        info = json.loads(raw.stdout)
    except FileNotFoundError:
        raise EngineError("FFPROBE_NOT_FOUND", "ffprobe is not installed or FFMPEG_BIN is misconfigured.")
    except subprocess.CalledProcessError as e:
        raise EngineError("INVALID_VIDEO", "The uploaded file could not be probed.", details={"stderr": e.stderr[-1000:]})
    except subprocess.TimeoutExpired:
        raise EngineError("PROBE_TIMEOUT", "Video inspection exceeded 30 seconds.", retryable=True)
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video:
        raise EngineError("NO_VIDEO_STREAM", "The file does not contain a video stream.")
    duration = float(info.get("format", {}).get("duration") or video.get("duration") or 0)
    fps_raw = video.get("avg_frame_rate", "30/1")
    try:
        num, den = [int(x) for x in fps_raw.split("/")]
        fps = num / den if den else 30
    except Exception:
        num, den, fps = 30, 1, 30
    audio = any(s.get("codec_type") == "audio" for s in streams)
    return {"duration_s": duration, "fps_num": num, "fps_den": den or 1, "fps": fps, "has_audio": audio,
            "width": int(video.get("width", 0)), "height": int(video.get("height", 0)),
            "video_codec": video.get("codec_name"), "audio_codec": next((s.get("codec_name") for s in streams if s.get("codec_type") == "audio"), None)}
