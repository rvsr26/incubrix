from __future__ import annotations
import json, subprocess, time, uuid, shlex
from pathlib import Path
from app.config import settings
from app.errors import EngineError
from app.timeline import duration, segment_duration, word_positions, timeline_hash


def _esc_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,").replace("%", "\\%")

def _atempo(speed: float) -> str:
    # atempo accepts factors in [0.5,2.0], chain factors for wider but supported speeds.
    factors=[]; x=speed
    while x < 0.5:
        factors.append(0.5); x/=0.5
    while x > 2.0:
        factors.append(2.0); x/=2.0
    factors.append(x)
    return ",".join(f"atempo={v:.8f}" for v in factors)

def render_timeline(source_path: Path, timeline: dict, transcript: list[dict], output_path: Path, manifest_path: Path) -> dict:
    start=time.perf_counter(); output_path.parent.mkdir(parents=True,exist_ok=True)
    if not timeline.get("segments"): raise EngineError("EMPTY_TIMELINE","There is no video content to render.")
    filters=[]; args=[settings.ffmpeg_bin,"-hide_banner","-y","-i",str(source_path)]
    # Current output positions for transcript words, used by captions/effects.
    positions=word_positions(timeline,transcript)
    for i,seg in enumerate(timeline["segments"]):
        a,b=float(seg["source_start"]),float(seg["source_end"]); speed=float(seg.get("speed",1.0))
        filters.append(f"[0:v]trim=start={a:.6f}:end={b:.6f},setpts=(PTS-STARTPTS)/{speed:.8f},setsar=1[v{i}]")
        out_audio=f"[a{i}]"
        if timeline.get("has_audio"):
            filters.append(f"[0:a]atrim=start={a:.6f}:end={b:.6f},asetpts=PTS-STARTPTS,{_atempo(speed)}{out_audio}")
        else:
            filters.append(f"anullsrc=channel_layout=stereo:sample_rate=48000,atrim=duration={((b-a)/speed):.6f},asetpts=PTS-STARTPTS{out_audio}")
    n=len(timeline["segments"])
    concat_inputs="".join(f"[v{i}][a{i}]" for i in range(n))
    filters.append(f"{concat_inputs}concat=n={n}:v=1:a=1[vbase][abase]")
    vlabel="vbase"
    # Word-anchored captions remain attached through edits because their anchors are word IDs.
    caption_filter_index=0
    for cap in timeline.get("captions",[]):
        spans=[]
        for wid in cap.get("word_ids",[]): spans.extend((a,b) for a,b,_ in positions.get(wid,[]))
        if not spans: continue
        spans=sorted(spans); groups=[]
        for a,b in spans:
            if groups and a-groups[-1][1] <= 0.75:
                groups[-1]=(groups[-1][0],max(groups[-1][1],b))
            else: groups.append((a,b))
        text=_esc_text(cap.get("text","")); size=int(cap.get("style",{}).get("font_size",36))
        color=cap.get("style",{}).get("color","white")
        for begin,end in groups:
            # Captions remain visible for ~0.7s when the anchored speech is very fast.
            if end-begin < 0.7: end=min(duration(timeline),begin+0.7)
            nxt=f"vcap{caption_filter_index}";caption_filter_index+=1
            filters.append(f"[{vlabel}]drawtext=text='{text}':fontsize={size}:fontcolor={color}:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-text_h-48:enable='between(t,{begin:.6f},{end:.6f})'[{nxt}]")
            vlabel=nxt
    # Word effects are resolved only at export, from the stable transcript word IDs.
    audio_label="abase"; effects=[]
    for effect in timeline.get("word_effects",[]):
        for a,b,_ in positions.get(effect["word_id"],[]): effects.append((a,b,effect["effect"]))
    for idx,(a,b,kind) in enumerate(effects):
        muted=f"amute{idx}";nxt=f"afx{idx}"
        filters.append(f"[{audio_label}]volume=0:enable='between(t,{a:.6f},{b:.6f})'[{muted}]")
        if kind=="bleep":
            delay=max(0,int(round(a*1000)))
            filters.append(f"aevalsrc=0.22*sin(2*PI*1000*t):s=48000:d={max(0.02,b-a):.6f}:c=stereo,adelay={delay}|{delay}[beep{idx}]")
            filters.append(f"[{muted}][beep{idx}]amix=inputs=2:duration=first:dropout_transition=0[{nxt}]")
        else:
            filters.append(f"[{muted}]anull[{nxt}]")
        audio_label=nxt
    if timeline.get("music") and timeline["music"].get("path") and timeline["music"].get("active",True):
        music_path=Path(timeline["music"]["path"])
        if music_path.exists():
            args += ["-stream_loop","-1","-i",str(music_path)]
            music_input="1:a"
            filters.append(f"[{music_input}]atrim=duration={duration(timeline):.6f},asetpts=PTS-STARTPTS,volume=0.12[musiclow]")
            # sidechaincompress lowers the music while the original voice is active.
            filters.append(f"[musiclow][{audio_label}]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[ducked]")
            filters.append(f"[{audio_label}][ducked]amix=inputs=2:duration=first:dropout_transition=2[aout]")
            audio_label="aout"
    # Force audio to the exact timeline duration after side-chain processing.
    # Some FFmpeg filter combinations otherwise inherit the longer music-input clock.
    expected_audio_duration=duration(timeline)
    filters.append(f"[{audio_label}]apad=whole_dur={expected_audio_duration:.6f},atrim=duration={expected_audio_duration:.6f},asetpts=PTS-STARTPTS[aoutfinal]")
    filters.append(f"[{vlabel}]format=yuv420p[vout]")
    graph=";".join(filters)
    args += ["-filter_complex",graph,"-map","[vout]","-map","[aoutfinal]","-r",str(timeline.get("fps",30)),"-c:v","mpeg4","-q:v","4","-c:a","aac","-b:a","160k","-movflags","+faststart",str(output_path)]
    try:
        proc=subprocess.run(args,capture_output=True,text=True,timeout=3600)
        if proc.returncode!=0:
            raise EngineError("RENDER_FAILED","FFmpeg could not render this timeline.",details={"stderr":proc.stderr[-3000:]})
    except FileNotFoundError:
        raise EngineError("FFMPEG_NOT_FOUND","ffmpeg is not installed or FFMPEG_BIN is misconfigured.")
    except subprocess.TimeoutExpired:
        raise EngineError("RENDER_TIMEOUT","The render exceeded one hour.",retryable=True)
    # Verify the produced file against the edit decision list before exposing it.
    try:
        probe=subprocess.run([settings.ffprobe_bin,"-v","error","-show_streams","-show_format","-of","json",str(output_path)],capture_output=True,text=True,check=True,timeout=30)
        probe_data=json.loads(probe.stdout)
        stream_info=probe_data.get("streams",[])
        v_stream=next((x for x in stream_info if x.get("codec_type")=="video"),None)
        a_stream=next((x for x in stream_info if x.get("codec_type")=="audio"),None)
        if not v_stream: raise EngineError("RENDER_VALIDATION_FAILED","Rendered output has no video stream.")
        expected=duration(timeline); frame=1.0/max(float(timeline.get("fps",30)),1.0)
        video_duration=float(v_stream.get("duration") or probe_data.get("format",{}).get("duration") or 0)
        audio_duration=float(a_stream.get("duration") or video_duration) if a_stream else video_duration
        if abs(video_duration-expected)>frame+0.002 or abs(audio_duration-video_duration)>frame+0.002:
            raise EngineError("RENDER_SYNC_VALIDATION_FAILED","Rendered output differs from the timeline or A/V sync exceeds one frame.",details={"expected_duration_s":expected,"video_duration_s":video_duration,"audio_duration_s":audio_duration,"frame_tolerance_s":frame})
    except EngineError: raise
    except Exception as exc:
        raise EngineError("RENDER_VALIDATION_FAILED","Could not validate the rendered MP4.",details={"reason":str(exc)})
    elapsed=(time.perf_counter()-start)*1000
    warnings=list(timeline.get("warnings",[]))
    manifest={
        "manifest_version":"1.0.0","project":"IncuEdit","timeline_hash":timeline_hash(timeline),
        "providers":{"transcription":{"name":"manual_or_mock_transcript","version":"1.0"},"instruction_parser":{"name":"deterministic_rules","version":"1.0"},"renderer":{"name":"FFmpeg","version":"runtime"}},
        "models":[],"settings":{"fps":timeline.get("fps"),"time_policy":timeline.get("time_policy"),"caption_count":len(timeline.get("captions",[])),"word_effect_count":len(effects)},
        "seed":0,"timings":{"render_ms":round(elapsed,2)},
        "sync_validation":{"expected_timeline_duration_s":round(expected,6),"video_stream_duration_s":round(video_duration,6),"audio_stream_duration_s":round(audio_duration,6),"max_offset_frames":round(abs(audio_duration-video_duration)*float(timeline.get("fps",30)),4),"max_length_difference_frames":round(abs(video_duration-expected)*float(timeline.get("fps",30)),4)},
        "cost_estimate":{"currency":"USD","amount":round((duration(timeline)/60)*settings.cost_estimate_usd_per_video_minute,6),"basis":"configured COST_ESTIMATE_USD_PER_VIDEO_MINUTE; excludes local compute"},
        "rights":{"source_sha256":timeline.get("source_sha256"),"source_rights":"user_attested_at_upload","generated_media":False},
        "warnings":warnings,"output":{"path":str(output_path.name),"duration_s":round(duration(timeline),3)}
    }
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest
