#!/usr/bin/env python3
"""Generate a synthetic, rights-clean 16-second test clip (color bars + tone, no real voice)."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"examples"/"demo_media.mp4"
OUT.parent.mkdir(parents=True,exist_ok=True)
cmd=["ffmpeg","-hide_banner","-y","-f","lavfi","-i","testsrc2=size=640x360:rate=30:duration=16","-f","lavfi","-i","sine=frequency=440:sample_rate=48000:duration=16","-c:v","mpeg4","-q:v","5","-pix_fmt","yuv420p","-c:a","aac","-shortest",str(OUT)]
subprocess.run(cmd,check=True)
print(OUT)
