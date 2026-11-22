from __future__ import annotations
from copy import deepcopy
import hashlib, json, math, re
from typing import Any
from app.errors import EngineError


def new_timeline(video_id: str, duration_s: float, fps: float, has_audio: bool, source_sha256: str) -> dict:
    return {
        "schema_version": "1.0.0", "video_id": video_id, "source_duration_s": round(duration_s, 6),
        "fps": round(fps, 6), "has_audio": bool(has_audio), "source_sha256": source_sha256,
        "time_policy": "current_timeline", "segments": [{"segment_id": "seg_0001", "source_start": 0.0, "source_end": round(duration_s, 6), "speed": 1.0}],
        "captions": [], "word_effects": [], "music": None, "history": [], "redo": [], "warnings": []
    }

def clone(tl: dict) -> dict:
    return deepcopy(tl)

def segment_duration(s: dict) -> float:
    return max(0.0, (s["source_end"] - s["source_start"]) / s.get("speed", 1.0))

def duration(tl: dict) -> float:
    return sum(segment_duration(s) for s in tl["segments"])

def timeline_hash(tl: dict) -> str:
    public = {k: v for k, v in tl.items() if k not in {"history", "redo", "warnings", "video_id"}}
    if isinstance(public.get("music"), dict):
        public["music"] = {k: v for k, v in public["music"].items() if k not in {"path", "filename"}}
    payload = json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()

def visible_slices(tl: dict, start: float, end: float) -> list[tuple[int, float, float]]:
    """Map current-timeline [start,end] into (segment index, source start, source end)."""
    if start < 0 or end <= start or end > duration(tl) + 1e-6:
        raise EngineError("TIME_OUT_OF_RANGE", "The requested time range is outside the current video.", details={"start": start, "end": end, "duration": duration(tl)})
    out, cursor = [], 0.0
    for idx, seg in enumerate(tl["segments"]):
        seg_d = segment_duration(seg)
        lo, hi = max(start, cursor), min(end, cursor + seg_d)
        if hi > lo + 1e-8:
            speed = seg.get("speed", 1.0)
            src_lo = seg["source_start"] + (lo - cursor) * speed
            src_hi = seg["source_start"] + (hi - cursor) * speed
            out.append((idx, src_lo, src_hi))
        cursor += seg_d
    return out

def _split_segment(seg: dict, cuts: list[tuple[float, float]]) -> list[dict]:
    pieces, cursor = [], seg["source_start"]
    for a, b in sorted(cuts):
        a, b = max(a, seg["source_start"]), min(b, seg["source_end"])
        if b <= a: continue
        if a > cursor + 1e-8:
            pieces.append({**seg, "source_start": cursor, "source_end": a})
        cursor = max(cursor, b)
    if cursor < seg["source_end"] - 1e-8:
        pieces.append({**seg, "source_start": cursor, "source_end": seg["source_end"]})
    return pieces

def cut_current(tl: dict, start: float, end: float) -> dict:
    slices = visible_slices(tl, start, end)
    cuts_by_index: dict[int, list[tuple[float,float]]] = {}
    for i, a, b in slices: cuts_by_index.setdefault(i, []).append((a,b))
    new_segments = []
    for i, seg in enumerate(tl["segments"]):
        new_segments.extend(_split_segment(seg, cuts_by_index.get(i, [])))
    if not new_segments:
        raise EngineError("WHOLE_VIDEO_CUT", "This edit would remove the entire video; it was rejected.")
    result = clone(tl); result["segments"] = _reid(new_segments)
    return result

def keep_current(tl: dict, start: float, end: float) -> dict:
    slices = visible_slices(tl, start, end)
    kept = []
    for i, a, b in slices:
        seg = tl["segments"][i]
        kept.append({**seg, "source_start": a, "source_end": b})
    if not kept: raise EngineError("EMPTY_KEEP_RANGE", "The requested keep range contains no video.")
    result = clone(tl); result["segments"] = _reid(kept)
    return result

def speed_current(tl: dict, start: float, end: float, speed: float) -> dict:
    if speed < 0.25 or speed > 4.0:
        raise EngineError("UNSUPPORTED_SPEED", "Speed must be between 0.25x and 4x.", details={"requested": speed})
    slices = visible_slices(tl, start, end)
    by_idx: dict[int, list[tuple[float,float]]] = {}
    for i,a,b in slices: by_idx.setdefault(i, []).append((a,b))
    out = []
    for i, seg in enumerate(tl["segments"]):
        cuts = sorted(by_idx.get(i, []))
        if not cuts: out.append(seg); continue
        cursor = seg["source_start"]
        for a,b in cuts:
            if a > cursor + 1e-8: out.append({**seg,"source_start":cursor,"source_end":a})
            out.append({**seg,"source_start":a,"source_end":b,"speed":speed})
            cursor = b
        if cursor < seg["source_end"] - 1e-8: out.append({**seg,"source_start":cursor,"source_end":seg["source_end"]})
    result = clone(tl); result["segments"] = _reid(out)
    return result

def reorder_current(tl: dict, start: float, end: float, target: float) -> dict:
    block = visible_slices(tl, start, end)
    extracted = []
    for i,a,b in block:
        extracted.append({**tl["segments"][i],"source_start":a,"source_end":b})
    remainder = cut_current(tl, start, end)
    if target < 0 or target > duration(remainder) + 1e-6:
        raise EngineError("TIME_OUT_OF_RANGE", "The new position is outside the remaining timeline.")
    pos_segments, tail_segments, cursor = [], [], 0.0
    for seg in remainder["segments"]:
        d = segment_duration(seg)
        if cursor + d <= target + 1e-8:
            pos_segments.append(seg)
        elif cursor >= target - 1e-8:
            tail_segments.append(seg)
        else:
            ratio = (target - cursor) * seg.get("speed", 1)
            split = seg["source_start"] + ratio
            pos_segments.append({**seg, "source_end": split})
            tail_segments.append({**seg, "source_start": split})
        cursor += d
    result = clone(tl)
    result["segments"] = _reid(pos_segments + extracted + tail_segments)
    return result

def _reid(segments: list[dict]) -> list[dict]:
    clean = []
    for s in segments:
        if s["source_end"] - s["source_start"] > 1e-7:
            clean.append({**s, "segment_id": f"seg_{len(clean)+1:04d}"})
    return clean

def word_positions(tl: dict, words: list[dict]) -> dict[str, list[tuple[float,float,dict]]]:
    positions = {}
    for w in words:
        found = []
        cursor = 0.0
        for seg in tl["segments"]:
            a = max(w["start"], seg["source_start"])
            b = min(w["end"], seg["source_end"])
            if b > a:
                rate = seg.get("speed", 1.0)
                found.append((cursor + (a - seg["source_start"]) / rate, cursor + (b - seg["source_start"]) / rate, w))
            cursor += segment_duration(seg)
        positions[w["word_id"]] = found
    return positions

def add_caption(tl: dict, text: str, word_ids: list[str], style: dict | None = None) -> dict:
    if not word_ids:
        raise EngineError("CAPTION_ANCHOR_REQUIRED", "A caption must be attached to at least one transcript word.")
    result = clone(tl)
    result["captions"].append({
        "caption_id": f"cap_{len(result['captions'])+1:04d}",
        "text": text,
        "start_word_id": word_ids[0],
        "end_word_id": word_ids[-1],
        "word_ids": word_ids,
        "style": style or {"font_size": 36, "color": "white", "position": "bottom"}
    })
    return result

def update_caption_style(tl: dict, color: str | None = None, font_size: int | None = None, font_size_delta: int | None = None) -> dict:
    if not tl.get("captions"):
        raise EngineError("CAPTION_NOT_FOUND", "There is no caption to modify.")
    result = clone(tl)
    for cap in result["captions"]:
        style = cap.setdefault("style", {"font_size": 36, "color": "white", "position": "bottom"})
        if color:
            style["color"] = color
        if font_size is not None:
            style["font_size"] = max(12, min(96, font_size))
        elif font_size_delta is not None:
            cur = int(style.get("font_size", 36))
            style["font_size"] = max(12, min(96, cur + font_size_delta))
    return result

def add_effect(tl: dict, word_ids: list[str], effect: str) -> dict:
    result = clone(tl)
    for wid in word_ids:
        result["word_effects"].append({"word_id": wid, "effect": effect})
    return result

def current_ranges_for_words(tl: dict, words: list[dict], word_ids: list[str]) -> list[tuple[float,float]]:
    pos = word_positions(tl, words)
    out = []
    for wid in word_ids:
        out.extend((a, b) for a, b, _ in pos.get(wid, []))
    return sorted(out)

def export_otio(tl: dict, video_filename: str | None = None) -> dict:
    """
    Exports the timeline to standard OpenTimelineIO (OTIO) JSON schema format (Timeline.1).
    Preserves clip order, source in/out points, speed effects (LinearTimeWarp.1),
    caption markers (Marker.1), and media references.
    """
    fps = float(tl.get("fps", 30.0)) or 30.0
    src_dur = float(tl.get("source_duration_s", duration(tl)))
    media_url = video_filename or f"video_{tl.get('video_id', 'source')}.mp4"
    
    video_clips = []
    audio_clips = []
    
    for seg in tl.get("segments", []):
        src_start = float(seg["source_start"])
        src_end = float(seg["source_end"])
        speed = float(seg.get("speed", 1.0))
        seg_src_dur = max(0.0, src_end - src_start)
        
        start_frame = round(src_start * fps)
        dur_frames = round(seg_src_dur * fps)
        
        effects = []
        if abs(speed - 1.0) > 1e-4:
            effects.append({
                "OTIO_SCHEMA": "LinearTimeWarp.1",
                "name": f"Speed_{speed:.2f}x",
                "time_scalar": speed,
                "metadata": {"speed_factor": speed}
            })
            
        media_ref = {
            "OTIO_SCHEMA": "ExternalReference.1",
            "target_url": media_url,
            "available_range": {
                "OTIO_SCHEMA": "TimeRange.1",
                "start_time": {"OTIO_SCHEMA": "RationalTime.1", "rate": fps, "value": 0.0},
                "duration": {"OTIO_SCHEMA": "RationalTime.1", "rate": fps, "value": round(src_dur * fps)}
            }
        }
        
        source_range = {
            "OTIO_SCHEMA": "TimeRange.1",
            "start_time": {"OTIO_SCHEMA": "RationalTime.1", "rate": fps, "value": float(start_frame)},
            "duration": {"OTIO_SCHEMA": "RationalTime.1", "rate": fps, "value": float(dur_frames)}
        }
        
        v_clip = {
            "OTIO_SCHEMA": "Clip.1",
            "name": seg["segment_id"],
            "source_range": source_range,
            "media_reference": media_ref,
            "effects": effects,
            "metadata": {"speed": speed, "source_start": src_start, "source_end": src_end}
        }
        video_clips.append(v_clip)
        
        a_clip = {
            "OTIO_SCHEMA": "Clip.1",
            "name": f"{seg['segment_id']}_audio",
            "source_range": source_range,
            "media_reference": media_ref,
            "effects": effects,
            "metadata": {"speed": speed}
        }
        audio_clips.append(a_clip)
        
    markers = []
    for cap in tl.get("captions", []):
        markers.append({
            "OTIO_SCHEMA": "Marker.1",
            "name": cap.get("text", "Caption"),
            "color": (cap.get("style", {}).get("color", "WHITE")).upper(),
            "marked_range": {
                "OTIO_SCHEMA": "TimeRange.1",
                "start_time": {"OTIO_SCHEMA": "RationalTime.1", "rate": fps, "value": 0.0},
                "duration": {"OTIO_SCHEMA": "RationalTime.1", "rate": fps, "value": round(fps)}
            },
            "metadata": {
                "caption_id": cap.get("caption_id"),
                "word_ids": cap.get("word_ids", []),
                "style": cap.get("style", {})
            }
        })
        
    otio_doc = {
        "OTIO_SCHEMA": "Timeline.1",
        "name": f"IncuEdit_{tl.get('video_id', 'export')}",
        "metadata": {
            "generator": "IncuEdit 1.0.0",
            "timeline_hash": timeline_hash(tl),
            "source_duration_s": src_dur,
            "current_duration_s": round(duration(tl), 4),
            "time_policy": tl.get("time_policy", "current_timeline")
        },
        "global_start_time": {
            "OTIO_SCHEMA": "RationalTime.1",
            "rate": fps,
            "value": 0.0
        },
        "tracks": {
            "OTIO_SCHEMA": "Stack.1",
            "name": "tracks",
            "children": [
                {
                    "OTIO_SCHEMA": "Track.1",
                    "name": "Video Track",
                    "kind": "Video",
                    "children": video_clips,
                    "markers": markers
                },
                {
                    "OTIO_SCHEMA": "Track.1",
                    "name": "Audio Track",
                    "kind": "Audio",
                    "children": audio_clips
                }
            ]
        }
    }
    return otio_doc
