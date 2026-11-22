from __future__ import annotations
import json
from pathlib import Path
import pytest
from app.timeline import new_timeline, duration, timeline_hash, cut_current, keep_current, speed_current, reorder_current, add_caption, word_positions
from app.engine import EditingEngine
from app.errors import EngineError
from app.parser import parse_time, parse_instruction

SOURCE_HASH="a"*64
WORDS=json.loads((Path(__file__).resolve().parents[1]/"examples"/"sample_transcript.json").read_text())

def make_session():
    return {"timeline":new_timeline("vid",16,30,True,SOURCE_HASH),"transcript":WORDS,"pending":None}

@pytest.mark.parametrize("value,expected",[
    ("0:00",0),("1:20",80),("2:05",125),("80 seconds",80),("10 sec",10),
    ("2 minutes",120),("1.5 minutes",90),("a minute twenty",80),("one minute",60),
    ("half a minute",30),("the beginning",0),("end",16),("last 10 seconds",6),
])
def test_parse_time(value,expected):
    assert parse_time(value,16)==pytest.approx(expected)

def test_cut_preserves_original_source_hash_and_shifts_content():
    tl=new_timeline("vid",16,30,True,SOURCE_HASH)
    edited=cut_current(tl,0,2)
    assert tl["source_sha256"]==edited["source_sha256"]==SOURCE_HASH
    assert duration(edited)==14
    assert edited["segments"][0]["source_start"]==2

def test_caption_word_ids_survive_cut_then_restore_intro():
    tl=new_timeline("vid",16,30,True,SOURCE_HASH)
    ids=[f"w{i:03d}" for i in range(1,5)]
    tl=add_caption(tl,"Welcome!",ids)
    removed=cut_current(tl,0,2)
    assert all(not word_positions(removed,WORDS).get(wid) for wid in ids)
    # Restore source interval [0,2] as a new source segment; anchors were not rewritten.
    restored={**removed,"segments":[{"segment_id":"seg_0001","source_start":0,"source_end":2,"speed":1},*removed["segments"]]}
    assert all(word_positions(restored,WORDS).get(wid) for wid in ids)
    assert restored["captions"][0]["word_ids"]==ids

def test_speed_changes_duration_and_keeps_source_anchor():
    tl=new_timeline("vid",16,30,True,SOURCE_HASH)
    sped=speed_current(tl,4,8,2)
    assert duration(sped)==14
    assert sped["segments"][1]["speed"]==2
    assert word_positions(sped,WORDS)["w009"]

def test_reorder_preserves_all_source_frames_once():
    tl=new_timeline("vid",16,30,True,SOURCE_HASH)
    moved=reorder_current(tl,5,7,1)
    ranges=sorted((round(s['source_start'],6),round(s['source_end'],6)) for s in moved['segments'])
    assert ranges==[(0,1),(1,5),(5,7),(7,16)]
    assert duration(moved)==16

def test_keep_range():
    tl=new_timeline("vid",16,30,True,SOURCE_HASH)
    kept=keep_current(tl,2,10)
    assert duration(kept)==8
    assert kept["segments"][0]["source_start"]==2

def test_timeline_hash_deterministic_and_excludes_history():
    tl=new_timeline("vid",16,30,True,SOURCE_HASH)
    a=timeline_hash(tl);tl["history"].append({"label":"ignored","timeline":{}})
    assert timeline_hash(tl)==a
    assert timeline_hash(new_timeline("different-random-session-id",16,30,True,SOURCE_HASH))==a

def test_whole_video_cut_rejected():
    tl=new_timeline("vid",16,30,True,SOURCE_HASH)
    with pytest.raises(EngineError,match="entire video"):
        cut_current(tl,0,16)

@pytest.mark.parametrize("instruction,op",[
    ("Cut the first 3 seconds","cut"),("Cut 2 seconds to 4 seconds","cut"),
    ("Cut the last 5 seconds","cut"),("Keep only from 1 seconds to 9 seconds","keep"),
    ("Speed up from 5 seconds to 8 seconds by 2x","speed"),
    ("Reorder section from 5 seconds to 7 seconds to 2 seconds","reorder"),
    ("Undo","undo"),("Redo","redo"),("Render","render"),
    ("Remove filler words","remove_fillers"),("Remove silences longer than 1 seconds","remove_silence"),
    ("Add a caption 'Hello' when I say welcome to the channel","caption"),
    ("Mute the word thanks","word_effect"),("Bleep the word thanks","word_effect"),
    ("Remove the part about pricing","semantic_cut"),("Auto-caption the whole video","auto_caption"),
    ("Add background music","music"),("Make that caption bigger","caption_resize"),
])
def test_instruction_parser(instruction,op):
    assert parse_instruction(instruction,16)["op"]==op

def test_caption_instruction_applies_and_is_three_way():
    s=make_session();r=EditingEngine().apply(s,"Add a caption 'Welcome!' when I say welcome to the channel")
    assert r["status"]=="applied"
    assert len(s["timeline"]["captions"])==1

def test_semantic_cut_requires_clarification_and_applies_answer():
    s=make_session();e=EditingEngine()
    r=e.apply(s,"Remove the part about pricing")
    assert r["status"]=="needs_clarification"
    assert len(r["options"])==3
    r=e.apply(s,"Remove the part about pricing","second one")
    assert r["status"]=="applied"
    assert duration(s["timeline"])<16

def test_undo_and_redo_are_single_history_steps():
    s=make_session();e=EditingEngine()
    assert e.apply(s,"Cut the first 2 seconds")["status"]=="applied"
    assert duration(s["timeline"])==14
    assert e.apply(s,"Undo")["status"]=="applied"
    assert duration(s["timeline"])==16
    assert e.apply(s,"Redo")["status"]=="applied"
    assert duration(s["timeline"])==14

def test_restore_intro_instruction_restores_removed_source_range():
    s=make_session();e=EditingEngine()
    assert e.apply(s,"Cut the first 3 seconds")["status"]=="applied"
    result=e.apply(s,"Actually, put the intro back")
    assert result["status"]=="applied"
    assert duration(s["timeline"])==16
    assert s["timeline"]["segments"][0]["source_start"]==0

def test_duplicate_destructive_instruction_is_safe():
    s=make_session();e=EditingEngine()
    e.apply(s,"Cut the first 2 seconds")
    r=e.apply(s,"Cut the first 2 seconds")
    assert r["status"]=="rejected"
    assert r["summary"]["code"]=="DUPLICATE_INSTRUCTION"
    assert duration(s["timeline"])==14

def test_unsupported_speed_rejected():
    s=make_session();r=EditingEngine().apply(s,"Speed up from 5 seconds to 8 seconds by 10x")
    assert r["status"]=="rejected"
    assert r["summary"]["code"]=="UNSUPPORTED_SPEED"

def test_unknown_prompt_rejected_without_mutation():
    s=make_session();before=timeline_hash(s["timeline"])
    r=EditingEngine().apply(s,"Make the video viral and emotional")
    assert r["status"]=="rejected"
    assert timeline_hash(s["timeline"])==before


def test_auto_caption_creates_word_id_anchors():
    s=make_session()
    result=EditingEngine().apply(s,"Auto-caption the whole video")
    assert result["status"]=="applied"
    assert s["timeline"]["captions"]
    assert all(c.get("word_ids") for c in s["timeline"]["captions"])
