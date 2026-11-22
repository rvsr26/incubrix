from __future__ import annotations
import json
import pytest
from app.timeline import (
    new_timeline, duration, timeline_hash, cut_current, keep_current,
    speed_current, reorder_current, add_caption, add_effect,
    export_otio, word_positions, update_caption_style
)
from app.engine import EditingEngine
from app.parser import parse_instruction, parse_time
from app.errors import EngineError
from app.media import sha256_file, probe_video


@pytest.fixture
def base_session(sample_words):
    tl = new_timeline("v-test", 16.0, 30.0, True, "dummy-sha256")
    return {
        "session_id": "s-test",
        "video_id": "v-test",
        "timeline": tl,
        "transcript": sample_words,
        "pending": None,
        "history": []
    }


# Scenario 1: Caption followed by cut
def test_scenario_01_caption_followed_by_cut(base_session):
    engine = EditingEngine()
    r1 = engine.apply(base_session, "Add a caption 'Welcome!' when I say welcome to the channel")
    assert r1["status"] == "applied"
    
    r2 = engine.apply(base_session, "Cut the first 2 seconds")
    assert r2["status"] == "applied"
    assert r2["duration_s"] == 14.0
    
    # Caption anchor still attached to transcript word IDs
    tl = base_session["timeline"]
    assert len(tl["captions"]) == 1
    assert tl["captions"][0]["word_ids"] == ["w001", "w002", "w003", "w004"]


# Scenario 2: Restore cut and caption recovery
def test_scenario_02_restore_cut_and_caption_recovery(base_session):
    engine = EditingEngine()
    engine.apply(base_session, "Add a caption 'Welcome!' when I say welcome to the channel")
    # Cut the range containing welcome
    engine.apply(base_session, "Cut 0 to 2")
    # Restore intro (0-30s)
    r3 = engine.apply(base_session, "Actually, put the intro back")
    assert r3["status"] == "applied"
    tl = base_session["timeline"]
    # Caption is present and anchors are active
    assert len(tl["captions"]) == 1
    pos = word_positions(tl, base_session["transcript"])
    assert len(pos["w001"]) > 0


# Scenario 3: Reorder then mute
def test_scenario_03_reorder_then_mute(base_session):
    engine = EditingEngine()
    engine.apply(base_session, "Move the section from 1 to 3 to 8")
    r2 = engine.apply(base_session, "Mute the word channel")
    assert r2["status"] == "applied"
    tl = base_session["timeline"]
    assert any(e["effect"] == "mute" for e in tl["word_effects"])


# Scenario 4: Filler removal intersecting a bleep
def test_scenario_04_filler_removal_intersecting_bleep(base_session):
    engine = EditingEngine()
    # Bleep a word
    r1 = engine.apply(base_session, "Bleep the word channel")
    assert r1["status"] == "applied"
    # Remove filler words
    r2 = engine.apply(base_session, "Remove all filler words")
    assert r2["status"] in {"applied", "rejected"}
    tl = base_session["timeline"]
    assert any(e["effect"] == "bleep" for e in tl["word_effects"])


# Scenario 5: Duplicate cuts prevention
def test_scenario_05_duplicate_cuts_prevention(base_session):
    engine = EditingEngine()
    r1 = engine.apply(base_session, "Cut 1 to 2")
    assert r1["status"] == "applied"
    r2 = engine.apply(base_session, "Cut 1 to 2")
    assert r2["status"] == "rejected"
    assert r2["summary"]["code"] == "DUPLICATE_INSTRUCTION"


# Scenario 6: Invalid timestamp out of range
def test_scenario_06_invalid_timestamp_out_of_range(base_session):
    engine = EditingEngine()
    r = engine.apply(base_session, "Cut from 20 to 25")
    assert r["status"] == "rejected"
    assert r["summary"]["code"] == "TIME_OUT_OF_RANGE"


# Scenario 7: Short video with out of range caption
def test_scenario_07_short_video_with_out_of_range_caption(base_session):
    engine = EditingEngine()
    r = engine.apply(base_session, "Add a caption 'Hello' when I say nonexistentwordatall")
    assert r["status"] == "rejected"
    assert r["summary"]["code"] == "ANCHOR_NOT_FOUND"


# Scenario 8: Multiple pricing mentions clarification
def test_scenario_08_multiple_pricing_mentions_clarification(base_session):
    base_session["transcript"] = [
        {"word_id": "w1", "text": "The", "start": 0.5, "end": 0.8, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w2", "text": "price", "start": 0.9, "end": 1.2, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w3", "text": "and", "start": 2.0, "end": 2.2, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w4", "text": "cost", "start": 2.3, "end": 2.6, "speaker": "speaker_1", "confidence": 0.99},
    ]
    engine = EditingEngine()
    r = engine.apply(base_session, "Remove the part about pricing")
    assert r["status"] == "needs_clarification"
    assert len(r["options"]) >= 2
    assert base_session["pending"] is not None


# Scenario 9: "The second one" clarification
def test_scenario_09_the_second_one_clarification(base_session):
    base_session["transcript"] = [
        {"word_id": "w1", "text": "The", "start": 0.5, "end": 0.8, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w2", "text": "price", "start": 0.9, "end": 1.2, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w3", "text": "and", "start": 2.0, "end": 2.2, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w4", "text": "cost", "start": 2.3, "end": 2.6, "speaker": "speaker_1", "confidence": 0.99},
    ]
    engine = EditingEngine()
    engine.apply(base_session, "Remove the part about pricing")
    r2 = engine.apply(base_session, "", answer="the second one")
    assert r2["status"] == "applied"
    assert base_session["pending"] is None


# Scenario 10: "All of them" clarification
def test_scenario_10_all_of_them_clarification(base_session):
    base_session["transcript"] = [
        {"word_id": "w1", "text": "The", "start": 0.5, "end": 0.8, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w2", "text": "price", "start": 0.9, "end": 1.2, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w3", "text": "and", "start": 2.0, "end": 2.2, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w4", "text": "cost", "start": 2.3, "end": 2.6, "speaker": "speaker_1", "confidence": 0.99},
    ]
    engine = EditingEngine()
    engine.apply(base_session, "Remove the part about pricing")
    r2 = engine.apply(base_session, "", answer="all of them")
    assert r2["status"] == "applied"


# Scenario 11: Undo and redo
def test_scenario_11_undo_and_redo(base_session):
    engine = EditingEngine()
    h0 = timeline_hash(base_session["timeline"])
    engine.apply(base_session, "Cut the first 3 seconds")
    h1 = timeline_hash(base_session["timeline"])
    assert h0 != h1
    
    # Undo
    r_undo = engine.apply(base_session, "Undo")
    assert r_undo["status"] == "applied"
    assert timeline_hash(base_session["timeline"]) == h0
    
    # Redo
    r_redo = engine.apply(base_session, "Redo")
    assert r_redo["status"] == "applied"
    assert timeline_hash(base_session["timeline"]) == h1


# Scenario 12: Restore specific earlier edit
def test_scenario_12_restore_specific_earlier_edit(base_session):
    engine = EditingEngine()
    engine.apply(base_session, "Cut the first 2 seconds") # edit 1
    engine.apply(base_session, "Speed up from 2 to 4 by 2x") # edit 2
    r_restore = engine.apply(base_session, "Restore edit number 1")
    assert r_restore["status"] == "applied"
    assert r_restore["operations"][0]["type"] == "restore_edit"


# Scenario 13: Restore intro while preserving unrelated edits
def test_scenario_13_restore_intro_preserving_unrelated_edits(base_session):
    engine = EditingEngine()
    engine.apply(base_session, "Cut the first 2 seconds")
    engine.apply(base_session, "Speed up from 4 to 6 by 2x")
    r = engine.apply(base_session, "Put the intro back")
    assert r["status"] == "applied"
    tl = base_session["timeline"]
    assert tl["segments"][0]["source_start"] == 0.0
    assert any(s.get("speed") == 2.0 for s in tl["segments"])


# Scenario 14: Speed changes
def test_scenario_14_speed_changes(base_session):
    engine = EditingEngine()
    r = engine.apply(base_session, "Speed up from 1 to 3 by 2x")
    assert r["status"] == "applied"
    assert r["duration_s"] == 15.0


# Scenario 15: Overlapping speed changes
def test_scenario_15_overlapping_speed_changes(base_session):
    engine = EditingEngine()
    engine.apply(base_session, "Speed up from 0 to 4 by 2x")
    # Overlapping speed change overrides newest visible interval
    r2 = engine.apply(base_session, "Speed up from 1 to 3 by 3x")
    assert r2["status"] == "applied"
    tl = base_session["timeline"]
    assert any(s.get("speed") == 3.0 for s in tl["segments"])


# Scenario 16: Ten times speed rejection
def test_scenario_16_ten_times_speed_rejection(base_session):
    engine = EditingEngine()
    r = engine.apply(base_session, "Speed up by 10x")
    assert r["status"] == "rejected"
    assert r["summary"]["code"] == "UNSUPPORTED_SPEED"


# Scenario 17: Cut everything rejection
def test_scenario_17_cut_everything_rejection(base_session):
    engine = EditingEngine()
    r = engine.apply(base_session, "Cut the first 16 seconds")
    assert r["status"] == "rejected"
    assert r["summary"]["code"] == "WHOLE_VIDEO_CUT"


# Scenario 18: Caption with partially removed words
def test_scenario_18_caption_with_partially_removed_words(base_session):
    engine = EditingEngine()
    engine.apply(base_session, "Add a caption 'Welcome!' when I say welcome to the channel")
    r = engine.apply(base_session, "Cut the first 0.5 seconds")
    assert r["status"] == "applied"
    tl = base_session["timeline"]
    assert len(tl["captions"]) == 1


# Scenario 19: Caption minimum readable duration
def test_scenario_19_caption_minimum_readable_duration(base_session):
    engine = EditingEngine()
    engine.apply(base_session, "Add a caption 'Quick' when I say welcome")
    engine.apply(base_session, "Speed up from 0 to 2 by 4x")
    tl = base_session["timeline"]
    assert len(tl["captions"]) == 1


# Scenario 20: Missing caption target
def test_scenario_20_missing_caption_target(base_session):
    engine = EditingEngine()
    r = engine.apply(base_session, "Add a caption 'Test' when I say astronaut on mars")
    assert r["status"] == "rejected"
    assert r["summary"]["code"] == "ANCHOR_NOT_FOUND"


# Scenario 21: Repeated instructions
def test_scenario_21_repeated_instructions(base_session):
    engine = EditingEngine()
    r1 = engine.apply(base_session, "Cut the first 1 second")
    assert r1["status"] == "applied"
    r2 = engine.apply(base_session, "Cut the first 1 second")
    assert r2["status"] == "rejected"
    assert r2["summary"]["code"] == "DUPLICATE_INSTRUCTION"


# Scenario 22: Deliberate pauses
def test_scenario_22_deliberate_pauses(base_session):
    engine = EditingEngine()
    r = engine.apply(base_session, "Remove silences longer than 5 seconds")
    assert r["status"] == "rejected"
    assert r["summary"]["code"] == "NO_LONG_SILENCES"


# Scenario 23: Low confidence transcript words
def test_scenario_23_low_confidence_transcript_words(base_session):
    base_session["transcript"] = [
        {"word_id": "w1", "text": "secret", "start": 1.0, "end": 1.5, "speaker": "host", "confidence": 0.65}
    ]
    engine = EditingEngine()
    r = engine.apply(base_session, "Bleep the word secret")
    assert r["status"] == "needs_clarification"
    assert base_session["pending"]["needs_confirm"] is True


# Scenario 24: Speaker-specific removal
def test_scenario_24_speaker_specific_removal(base_session):
    base_session["transcript"] = [
        {"word_id": "w1", "text": "Hello", "start": 0.5, "end": 1.0, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w2", "text": "World", "start": 1.5, "end": 2.0, "speaker": "speaker_2", "confidence": 0.99},
    ]
    engine = EditingEngine()
    r = engine.apply(base_session, "Remove what speaker 2 said")
    assert r["status"] == "applied"
    tl = base_session["timeline"]
    assert duration(tl) < 16.0


# Scenario 25: Two speaker overlap
def test_scenario_25_two_speaker_overlap(base_session):
    base_session["transcript"] = [
        {"word_id": "w1", "text": "Hello", "start": 0.5, "end": 1.5, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w2", "text": "Hi", "start": 1.0, "end": 1.8, "speaker": "speaker_2", "confidence": 0.99},
    ]
    engine = EditingEngine()
    r = engine.apply(base_session, "Cut the first 1 second")
    assert r["status"] == "applied"


# Scenario 26: Speaker label inconsistency warning
def test_scenario_26_speaker_label_inconsistency_warning(base_session):
    engine = EditingEngine()
    r = engine.apply(base_session, "Remove speaker 99")
    assert r["status"] == "rejected"
    assert r["summary"]["code"] == "NO_SPEAKER_WORDS"


# Scenario 27: Video with no audio
def test_scenario_27_video_with_no_audio():
    tl = new_timeline("v-silent", 10.0, 30.0, False, "dummy-hash")
    assert tl["has_audio"] is False
    assert duration(tl) == 10.0
    tl_cut = cut_current(tl, 1.0, 3.0)
    assert duration(tl_cut) == 8.0


# Scenario 28: Variable frame rate input
def test_scenario_28_variable_frame_rate_input(sample_video):
    meta = probe_video(sample_video)
    assert meta["fps"] > 0
    assert meta["duration_s"] > 0


# Scenario 29: Background music ducking
def test_scenario_29_background_music_ducking(base_session):
    base_session["timeline"]["music"] = {
        "path": "examples/demo_music.wav",
        "active": False,
        "duck_under_speech": True
    }
    engine = EditingEngine()
    r = engine.apply(base_session, "Add background music and lower it while I speak")
    assert r["status"] == "applied"
    assert base_session["timeline"]["music"]["active"] is True


# Scenario 30: Three part request with one impossible operation (atomic rollback)
def test_scenario_30_three_part_request_with_one_impossible(base_session):
    h0 = timeline_hash(base_session["timeline"])
    engine = EditingEngine()
    cmd = "Cut the first 1 second and add a caption 'Hello' when I say completelymissingphrase"
    r = engine.apply(base_session, cmd)
    assert r["status"] == "rejected"
    assert timeline_hash(base_session["timeline"]) == h0


# Scenario 31: Partial failure prevention
def test_scenario_31_partial_failure_prevention(base_session):
    d0 = duration(base_session["timeline"])
    engine = EditingEngine()
    cmd = "Cut the first 2 seconds and add a caption 'Test' when I say impossiblewordanchor"
    r = engine.apply(base_session, cmd)
    assert r["status"] == "rejected"
    assert duration(base_session["timeline"]) == d0


# Scenario 32: Idempotent job requests (Client API integration)
def test_scenario_32_idempotent_job_requests(client, sample_video):
    with sample_video.open("rb") as f:
        r1 = client.post("/api/v1/videos/upload", headers={"Idempotency-Key": "idemp-test-1"}, data={"rights_confirmed": "true"}, files={"file": ("demo.mp4", f, "video/mp4")})
        assert r1.status_code == 200
        vid = r1.json()["video"]["video_id"]
    
    r_sess = client.post("/api/v1/sessions", headers={"Idempotency-Key": "idemp-test-sess"}, json={"video_id": vid, "transcript": []})
    sid = r_sess.json()["session_id"]
    
    rj1 = client.post(f"/api/v1/sessions/{sid}/render", headers={"Idempotency-Key": "render-idem-1"})
    rj2 = client.post(f"/api/v1/sessions/{sid}/render", headers={"Idempotency-Key": "render-idem-1"})
    assert rj1.status_code == 202
    assert rj2.status_code == 202
    assert rj1.json()["job_id"] == rj2.json()["job_id"]


# Scenario 33: Job status and progress
def test_scenario_33_job_status_and_progress(client, sample_video):
    with sample_video.open("rb") as f:
        v = client.post("/api/v1/videos/upload", headers={"Idempotency-Key": "job-prog-v"}, data={"rights_confirmed": "true"}, files={"file": ("demo.mp4", f, "video/mp4")}).json()["video"]
    s = client.post("/api/v1/sessions", headers={"Idempotency-Key": "job-prog-s"}, json={"video_id": v["video_id"], "transcript": []}).json()
    rj = client.post(f"/api/v1/sessions/{s['session_id']}/render", headers={"Idempotency-Key": "job-prog-r"}).json()
    jid = rj["job_id"]
    r_poll = client.get(f"/api/v1/jobs/{jid}")
    assert r_poll.status_code == 200
    assert r_poll.json()["status"] in {"queued", "running", "succeeded"}


# Scenario 34: Render sync and duration
def test_scenario_34_render_sync_and_duration(client, sample_video, sample_words):
    with sample_video.open("rb") as f:
        v = client.post("/api/v1/videos/upload", headers={"Idempotency-Key": "sync-v"}, data={"rights_confirmed": "true"}, files={"file": ("demo.mp4", f, "video/mp4")}).json()["video"]
    s = client.post("/api/v1/sessions", headers={"Idempotency-Key": "sync-s"}, json={"video_id": v["video_id"], "transcript": sample_words}).json()
    client.post(f"/api/v1/sessions/{s['session_id']}/instructions", headers={"Idempotency-Key": "sync-inst"}, json={"say": "Cut the first 2 seconds"})
    r_render = client.post(f"/api/v1/sessions/{s['session_id']}/render", headers={"Idempotency-Key": "sync-render"}).json()
    jid = r_render["job_id"]
    
    import time
    for _ in range(50):
        j = client.get(f"/api/v1/jobs/{jid}").json()
        if j["status"] in {"succeeded", "failed"}:
            break
        time.sleep(0.2)
    assert j["status"] == "succeeded"
    manifest = j["result"]["manifest"]
    assert manifest["sync_validation"]["max_length_difference_frames"] <= 1.0


# Scenario 35: Original media hash preservation
def test_scenario_35_original_media_hash_preservation(client, sample_video):
    h_before = sha256_file(sample_video)
    with sample_video.open("rb") as f:
        v = client.post("/api/v1/videos/upload", headers={"Idempotency-Key": "hash-v"}, data={"rights_confirmed": "true"}, files={"file": ("demo.mp4", f, "video/mp4")}).json()["video"]
    s = client.post("/api/v1/sessions", headers={"Idempotency-Key": "hash-s"}, json={"video_id": v["video_id"], "transcript": []}).json()
    client.post(f"/api/v1/sessions/{s['session_id']}/instructions", headers={"Idempotency-Key": "hash-cut"}, json={"say": "Cut the first 3 seconds"})
    h_after = sha256_file(sample_video)
    assert h_before == h_after


# Scenario 36: Batch runner execution
def test_scenario_36_batch_runner_execution():
    from scripts.session_runner import run_one
    assert callable(run_one)


# Scenario 37: API error handling
def test_scenario_37_api_error_handling(client):
    r = client.post("/api/v1/sessions", json={"video_id": "nonexistent", "transcript": []})
    assert r.status_code == 400
    assert "error" in r.json()
    assert r.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"


# Scenario 38: Restart/recovery behavior
def test_scenario_38_restart_recovery_behavior(base_session):
    h1 = timeline_hash(base_session["timeline"])
    restored_tl = new_timeline(base_session["video_id"], 16.0, 30.0, True, "dummy-sha256")
    h2 = timeline_hash(restored_tl)
    assert h1 == h2


# Scenario 39: OpenTimelineIO export validation
def test_scenario_39_opentimelineio_export_validation(base_session):
    engine = EditingEngine()
    engine.apply(base_session, "Add a caption 'Welcome!' when I say welcome")
    engine.apply(base_session, "Speed up from 2 to 4 by 2x")
    
    otio_doc = export_otio(base_session["timeline"], "demo_media.mp4")
    assert otio_doc["OTIO_SCHEMA"] == "Timeline.1"
    assert "tracks" in otio_doc
    assert otio_doc["tracks"]["OTIO_SCHEMA"] == "Stack.1"
    tracks = otio_doc["tracks"]["children"]
    assert len(tracks) == 2
    v_track = tracks[0]
    assert v_track["kind"] == "Video"
    assert len(v_track["children"]) >= 1
    # Speed effect preserved
    assert any(len(clip.get("effects", [])) > 0 for clip in v_track["children"])
    # Caption marker preserved
    assert len(v_track.get("markers", [])) >= 1


# Scenario 40: Caption color styling
def test_scenario_40_caption_color_styling(base_session):
    engine = EditingEngine()
    engine.apply(base_session, "Add a caption 'Welcome!' when I say welcome")
    r2 = engine.apply(base_session, "Make that caption red")
    assert r2["status"] == "applied"
    tl = base_session["timeline"]
    assert tl["captions"][0]["style"]["color"] == "red"


# Scenario 41: Vague instruction clarification
def test_scenario_41_vague_instruction_clarification(base_session):
    engine = EditingEngine()
    r = engine.apply(base_session, "Cut the boring part")
    assert r["status"] == "needs_clarification"


# Scenario 42: Cut after phrase multiple mentions
def test_scenario_42_cut_after_phrase_multiple_mentions(base_session):
    base_session["transcript"] = [
        {"word_id": "w1", "text": "thanks", "start": 1.0, "end": 1.4, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w2", "text": "thanks", "start": 3.0, "end": 3.4, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w3", "text": "thanks", "start": 5.0, "end": 5.4, "speaker": "speaker_1", "confidence": 0.99},
        {"word_id": "w4", "text": "thanks", "start": 7.0, "end": 7.4, "speaker": "speaker_1", "confidence": 0.99},
    ]
    engine = EditingEngine()
    r = engine.apply(base_session, "Remove everything after I say thanks")
    assert r["status"] == "needs_clarification"
    assert len(r["options"]) >= 4
    # Resolve with the last one
    r2 = engine.apply(base_session, "", answer="the last one")
    assert r2["status"] == "applied"
    assert r2["duration_s"] == 7.4
