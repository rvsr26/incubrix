#!/usr/bin/env python3
"""Run one scripted IncuEdit session or a directory of sessions against the API."""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import httpx, yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def read_session(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) if path.suffix.lower() in {".yaml", ".yml"} else json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("steps"), list):
        raise ValueError("Session file must contain a 'steps' array.")
    return data

def normalize_answer(answer):
    """Keep YAML 1.1 booleans useful as human yes/no clarification replies."""
    if answer is None: return None
    if isinstance(answer, bool): return "yes" if answer else "no"
    return str(answer)

def request(client, method, url, key, **kwargs):
    headers = kwargs.pop("headers", {})
    headers["Idempotency-Key"] = key
    r = client.request(method, url, headers=headers, **kwargs)
    if r.status_code >= 400:
        try: detail = r.json()
        except Exception: detail = r.text
        raise RuntimeError(f"{method} {url} returned {r.status_code}: {detail}")
    return r

def get_client(base_url: str):
    """Returns an httpx.Client if live API is reachable, else falls back to in-process TestClient."""
    base_url = base_url.rstrip("/")
    try:
        c = httpx.Client(timeout=120)
        r = c.get(f"{base_url}/api/v1/health", timeout=1.0)
        if r.status_code == 200:
            return c, base_url
    except Exception:
        pass
    
    # In-process TestClient fallback
    from starlette.testclient import TestClient
    from app.main import app
    return TestClient(app, base_url="http://testserver"), "http://testserver"

def run_one(path: Path, base_url: str, out_dir: Path) -> dict:
    spec = read_session(path)
    out_dir.mkdir(parents=True, exist_ok=True)
    client, target_url = get_client(base_url)
    
    video_value = spec.get("video")
    if not video_value: raise ValueError("Session requires a local 'video' path.")
    if str(video_value).startswith("https://"):
        up = request(client, "POST", target_url + "/api/v1/videos/from-url", f"{path.stem}-upload", data={"url": str(video_value), "rights_confirmed": "true"})
    else:
        video_path = (path.parent / str(video_value)).resolve()
        with video_path.open("rb") as f:
            up = request(client, "POST", target_url + "/api/v1/videos/upload", f"{path.stem}-upload", files={"file": (video_path.name, f, "video/mp4")}, data={"rights_confirmed": "true"})
    video = up.json()["video"]
    
    transcript = spec.get("transcript", [])
    if isinstance(transcript, str):
        transcript = json.loads((path.parent / transcript).read_text(encoding="utf-8"))
    if isinstance(transcript, dict):
        transcript = transcript.get("words", [])
        
    sr = request(client, "POST", target_url + "/api/v1/sessions", f"{path.stem}-session", json={"video_id": video["video_id"], "transcript": transcript})
    session_id = sr.json()["session_id"]
    
    if spec.get("music"):
        music_path = (path.parent / str(spec["music"])).resolve()
        with music_path.open("rb") as mf:
            music_response = request(client, "POST", f"{target_url}/api/v1/sessions/{session_id}/music", f"{path.stem}-music", files={"file": (music_path.name, mf, "audio/wav")}, data={"rights_confirmed": "true"}).json()
    else:
        music_response = None
        
    results = []
    for idx, step in enumerate(spec["steps"], 1):
        if "restore_history_index" in step:
            payload = {"restore_history_index": step["restore_history_index"]}
            response = request(client, "POST", f"{target_url}/api/v1/sessions/{session_id}/restore", f"{path.stem}-step-{idx}", json={"history_index": step["restore_history_index"]}).json()
        else:
            answer = normalize_answer(step.get("answer"))
            payload = {"say": step.get("say", ""), "answer": answer}
            response = request(client, "POST", f"{target_url}/api/v1/sessions/{session_id}/instructions", f"{path.stem}-step-{idx}", json=payload).json()
        results.append({"step": idx, "input": payload, "response": response})
        
        if payload.get("say", "").strip().lower() == "render" and response.get("status") == "applied":
            job = request(client, "POST", f"{target_url}/api/v1/sessions/{session_id}/render", f"{path.stem}-render").json()
            for _ in range(3600):
                state = client.get(f"{target_url}/api/v1/jobs/{job['job_id']}").json()
                if state["status"] in {"succeeded", "failed"}: break
                time.sleep(0.5)
            if state["status"] == "succeeded":
                video_bytes = client.get(f"{target_url}/api/v1/jobs/{job['job_id']}/video").content
                (out_dir / f"{path.stem}_render.mp4").write_bytes(video_bytes)
                manifest_bytes = client.get(f"{target_url}/api/v1/jobs/{job['job_id']}/manifest").content
                (out_dir / f"{path.stem}_manifest.json").write_bytes(manifest_bytes)
                results[-1]["render_job"] = state
            else:
                results[-1]["render_job"] = state
                
    timeline = client.get(f"{target_url}/api/v1/sessions/{session_id}/timeline").json()
    result = {
        "session_file": path.name,
        "video": {k: v for k, v in video.items() if k != "path"},
        "session_id": session_id,
        "music_upload": music_response,
        "steps": results,
        "final_timeline": timeline["timeline"],
        "timeline_hash": timeline["timeline_hash"],
        "duration_s": timeline["duration_s"]
    }
    (out_dir / f"{path.stem}_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out_dir / f"{path.stem}_timeline.json").write_text(json.dumps(timeline["timeline"], indent=2), encoding="utf-8")
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="One YAML/JSON session file or a directory containing session files")
    p.add_argument("--api-url", default="http://localhost:8000")
    p.add_argument("--output", type=Path, default=Path("./session-results"))
    args = p.parse_args()
    paths = sorted(x for x in args.input.iterdir() if x.suffix.lower() in {".yaml", ".yml", ".json"}) if args.input.is_dir() else [args.input]
    all_results = []
    for path in paths:
        try:
            print(f"Running {path.name} ...")
            all_results.append(run_one(path, args.api_url, args.output))
            print(f"  OK · duration={all_results[-1]['duration_s']}s · hash={all_results[-1]['timeline_hash'][:12]}")
        except Exception as e:
            failure = {"session_file": path.name, "error": str(e), "status": "failed"}
            all_results.append(failure)
            (args.output / f"{path.stem}_failure.json").parent.mkdir(parents=True, exist_ok=True)
            (args.output / f"{path.stem}_failure.json").write_text(json.dumps(failure, indent=2), encoding="utf-8")
            print(f"  FAILED · {e}")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "results.json").write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_results)} result(s) to {args.output.resolve()}")
    if any(x.get("status") == "failed" for x in all_results): raise SystemExit(1)

if __name__ == "__main__":
    main()
