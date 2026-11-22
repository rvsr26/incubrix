"""Verify 3-round determinism across all 20 test sessions."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_BASE = ROOT / "artifacts" / "determinism_final"
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

rounds = ["round1", "round2", "round3"]
round_results: dict[str, dict[str, str]] = {}

for r in rounds:
    out_dir = OUTPUT_BASE / r
    results_path = out_dir / "results.json"
    if not results_path.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"=== Running {r} ===")
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "session_runner.py"),
            str(ROOT / "examples" / "sessions"),
            "--output",
            str(out_dir),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error in {r}: {res.stderr}")
            sys.exit(1)
    
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    hashes = {}
    for entry in data:
        session = entry.get("session_file")
        h = entry.get("timeline_hash")
        dur = entry.get("duration_s")
        hashes[session] = {"hash": h, "duration": dur}
    round_results[r] = hashes

# Compare hashes across rounds
all_sessions = sorted(list(round_results["round1"].keys()))
discrepancies = []
summary = {}

for s in all_sessions:
    h1 = round_results["round1"][s]["hash"]
    h2 = round_results["round2"][s]["hash"]
    h3 = round_results["round3"][s]["hash"]
    dur = round_results["round1"][s]["duration"]
    match = (h1 == h2 == h3) and (h1 is not None)
    if not match:
        discrepancies.append({
            "session": s,
            "round1": h1,
            "round2": h2,
            "round3": h3,
        })
    summary[s] = {
        "hash": h1,
        "duration_s": dur,
        "round1_hash": h1,
        "round2_hash": h2,
        "round3_hash": h3,
        "is_deterministic": match,
    }

report = {
    "total_sessions": len(all_sessions),
    "rounds_executed": 3,
    "deterministic_sessions": len(all_sessions) - len(discrepancies),
    "discrepancies_count": len(discrepancies),
    "determinism_percentage": 100.0 if not discrepancies else ((len(all_sessions) - len(discrepancies)) / len(all_sessions)) * 100.0,
    "discrepancies": discrepancies,
    "sessions": summary,
}

report_path = OUTPUT_BASE / "report.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("\n=== Determinism Verification Result ===")
print(f"Total sessions: {len(all_sessions)}")
det_count = report["deterministic_sessions"]
det_pct = report["determinism_percentage"]
print(f"Deterministic: {det_count}/{len(all_sessions)} ({det_pct}%)")
if discrepancies:
    print(f"FAILED: {len(discrepancies)} discrepancies found:")
    for d in discrepancies:
        print(f"  {d['session']}: r1={d['round1']} r2={d['round2']} r3={d['round3']}")
    sys.exit(1)
else:
    print("SUCCESS: 100% bitwise timeline determinism verified across all 3 rounds!")
    for s, info in summary.items():
        print(f"  {s}: dur={info['duration_s']}s hash={info['hash'][:12]} (match={info['is_deterministic']})")
