from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import re, time
from app.errors import EngineError
from app.parser import parse_instruction, parse_single_instruction, find_word_matches
from app.timeline import (
    clone, duration, timeline_hash, cut_current, keep_current, speed_current,
    reorder_current, add_caption, update_caption_style, add_effect,
    word_positions, segment_duration
)


def _snapshot(tl: dict) -> dict:
    return {k: deepcopy(v) for k, v in tl.items() if k not in {"history", "redo"}}

def _save_edit(before: dict, after: dict, label: str) -> dict:
    after["history"] = deepcopy(before.get("history", [])) + [{"label": label, "timeline": _snapshot(before)}]
    after["redo"] = []
    return after

def _visible_word_groups(tl: dict, words: list[dict], phrase: str) -> list[list[dict]]:
    matches = find_word_matches(words, phrase, tl)
    pos = word_positions(tl, words)
    return [g for g in matches if any(pos.get(w["word_id"]) for w in g)]

def _remove_source_ranges(tl: dict, ranges: list[tuple[float, float]]) -> dict:
    ranges = sorted(ranges)
    if not ranges:
        return clone(tl)
    out = []
    for seg in tl["segments"]:
        cursor = seg["source_start"]
        for a, b in ranges:
            a = max(a, seg["source_start"])
            b = min(b, seg["source_end"])
            if b <= a or b <= cursor:
                continue
            if a > cursor + 1e-8:
                out.append({**seg, "source_start": cursor, "source_end": a})
            cursor = max(cursor, b)
        if cursor < seg["source_end"] - 1e-8:
            out.append({**seg, "source_start": cursor, "source_end": seg["source_end"]})
    if not out:
        raise EngineError("WHOLE_VIDEO_CUT", "This edit would remove the entire video; it was rejected.")
    result = clone(tl)
    result["segments"] = [{**s, "segment_id": f"seg_{i+1:04d}"} for i, s in enumerate(out)]
    return result

def _word_is_filler(words: list[dict], i: int) -> bool:
    token = words[i].get("text", words[i].get("word", "")).strip(".,!?;:").lower()
    if token in {"um", "uh", "erm", "er"}:
        return True
    if token != "like":
        return False
    prev = words[i - 1] if i else None
    nxt = words[i + 1] if i + 1 < len(words) else None
    gap = (words[i]["start"] - prev["end"]) if prev else 99
    # Do not strip idiomatic "looks like", "would like", "feel like", etc.
    if prev and prev.get("text", prev.get("word", "")).lower().strip(".,!?") in {
        "looks", "looked", "sound", "sounds", "feel", "feels", "felt",
        "would", "could", "should", "I'd", "i'd", "something", "things", "people"
    }:
        return False
    return i == 0 or gap >= 0.22 or (prev and prev.get("text", prev.get("word", "")).lower() in {"and", "so", "well", "but"}) or (nxt and nxt.get("text", nxt.get("word", "")).lower() in {"um", "uh"})


class EditingEngine:
    def apply(self, session: dict, instruction: str, answer: str | None = None) -> dict:
        start_time = time.perf_counter()
        tl = session["timeline"]
        words = session.get("transcript", [])
        
        # 1. Resolve any pending clarification
        if session.get("pending"):
            pending = session["pending"]
            if not answer:
                return self._clarify(pending["question"], pending["options"], tl, "A clarification is waiting for your selection.")
            choice = answer.strip().lower()
            selected = None
            
            # Handle cut after phrase clarification
            if pending.get("cut_after"):
                groups = pending["groups"]
                if choice in {"last", "the last one", "last one", "4th", "fourth", "4"}:
                    selected = [groups[-1]]
                else:
                    m = re.search(r"(?:first|1st|1|second|2nd|2|third|3rd|3|fourth|4th|4)", choice)
                    if m:
                        idx_map = {"first": 1, "1st": 1, "1": 1, "second": 2, "2nd": 2, "2": 2, "third": 3, "3rd": 3, "3": 3, "fourth": 4, "4th": 4, "4": 4}
                        n = idx_map.get(m.group(0), 1)
                        if 1 <= n <= len(groups):
                            selected = [groups[n - 1]]
                if selected is None:
                    return self._clarify(pending["question"], pending["options"], tl, "Please choose one occurrence (e.g. 'the second one' or 'the last one').")
                before = clone(tl)
                pos = word_positions(tl, words)
                ranges = pos.get(selected[0][-1]["word_id"], [])
                if not ranges:
                    raise EngineError("PHRASE_NOT_VISIBLE", "Selected phrase is no longer visible in current timeline.")
                current_cut_point = ranges[-1][1]
                after = cut_current(tl, current_cut_point, duration(tl))
                operation = {"type": "cut_after_phrase", "phrase": pending.get("phrase", ""), "from_time_s": current_cut_point}
                session["timeline"] = _save_edit(before, after, "cut after phrase")
                session["pending"] = None
                return self._applied(session, [operation], "Cut everything after the selected phrase occurrence.")

            if pending.get("needs_confirm") and choice in {"yes", "confirm", "yes, apply", "bleep anyway", "proceed"}:
                selected = pending["groups"]
            elif choice in {"all", "all of them", "every one"}:
                selected = pending["groups"]
            else:
                m = re.search(r"(?:first|1st|1|second|2nd|2|third|3rd|3|fourth|4th|4)", choice)
                if m:
                    idx_map = {"first": 1, "1st": 1, "1": 1, "second": 2, "2nd": 2, "2": 2, "third": 3, "3rd": 3, "3": 3, "fourth": 4, "4th": 4, "4": 4}
                    n = idx_map[m.group(0)]
                    if 1 <= n <= len(pending["groups"]):
                        selected = [pending["groups"][n - 1]]
            if selected is None:
                return self._clarify(pending["question"], pending["options"], tl, "Please choose one listed occurrence or say 'all'.")
            
            before = clone(tl)
            if pending.get("effect"):
                ids = [w["word_id"] for g in selected for w in g]
                after = add_effect(tl, ids, pending["effect"])
                operation = {"type": pending["effect"], "word_ids": ids}
                message = f"Applied {pending['effect']} to the selected word occurrence(s)."
            else:
                ranges = [(g[0]["start"], g[-1]["end"]) for g in selected]
                after = _remove_source_ranges(tl, ranges)
                operation = {"type": "cut_words", "word_ids": [w["word_id"] for g in selected for w in g]}
                message = "Removed the selected transcript occurrence(s)."
            session["timeline"] = _save_edit(before, after, "resolve clarification")
            session["pending"] = None
            return self._applied(session, [operation], message)

        # 2. Parse new instruction
        try:
            parsed = parse_instruction(instruction, duration(tl))
            op = parsed["op"]
            signature = __import__("json").dumps(parsed, sort_keys=True, separators=(",", ":"))
            if op in {"cut", "semantic_cut", "remove_fillers", "remove_silence"} and session.get("last_success_signature") == signature:
                raise EngineError("DUPLICATE_INSTRUCTION", "This exact destructive instruction was just applied. No second edit was made.")
            
            if op == "render":
                return {
                    "status": "applied",
                    "operations": [{"type": "render"}],
                    "summary": {
                        "before_duration_s": round(duration(tl), 3),
                        "after_duration_s": round(duration(tl), 3),
                        "message": "Render requested; use the render endpoint or CLI to export the timeline."
                    },
                    "question": None, "options": [],
                    "timeline_hash": timeline_hash(tl),
                    "duration_s": round(duration(tl), 3)
                }

            if op == "undo":
                if not tl.get("history"):
                    raise EngineError("NOTHING_TO_UNDO", "There is no earlier edit to undo.")
                old = clone(tl)
                entry = tl["history"][-1]
                restored = clone(entry["timeline"])
                restored["history"] = deepcopy(tl["history"][:-1])
                restored["redo"] = deepcopy(tl.get("redo", [])) + [{"label": entry["label"], "timeline": _snapshot(old)}]
                session["timeline"] = restored
                return self._applied(session, [{"type": "undo", "edit": entry["label"]}], f"Undid: {entry['label']}.", before=duration(old))

            if op == "redo":
                if not tl.get("redo"):
                    raise EngineError("NOTHING_TO_REDO", "There is no edit available to redo.")
                old = clone(tl)
                entry = tl["redo"][-1]
                restored = clone(entry["timeline"])
                restored["history"] = deepcopy(tl.get("history", [])) + [{"label": entry["label"], "timeline": _snapshot(old)}]
                restored["redo"] = deepcopy(tl["redo"][:-1])
                session["timeline"] = restored
                return self._applied(session, [{"type": "redo", "edit": entry["label"]}], f"Redid: {entry['label']}.", before=duration(old))

            if op == "vague_instruction":
                return self._clarify(
                    "Could you specify which part, phrase, or exact time range you would like to edit?",
                    [
                        {"id": 1, "label": "Provide time range (e.g., 'Cut 0:00 to 0:30')"},
                        {"id": 2, "label": "Provide phrase (e.g., 'Remove the section about pricing')"}
                    ],
                    tl,
                    "Ambiguous instruction received; no destructive edit made."
                )

            # Handle compound multi-part instructions with atomic rollback
            if op == "compound":
                working_tl = clone(tl)
                compound_ops = []
                for sub_op_dict in parsed["operations"]:
                    sub_op = sub_op_dict["op"]
                    if sub_op == "cut":
                        working_tl = cut_current(working_tl, sub_op_dict["start"], sub_op_dict["end"])
                        compound_ops.append({"type": "cut", "current_start": sub_op_dict["start"], "current_end": sub_op_dict["end"]})
                    elif sub_op == "caption":
                        groups = _visible_word_groups(working_tl, words, sub_op_dict["anchor"])
                        if not groups:
                            raise EngineError("ANCHOR_NOT_FOUND", f"Could not find anchor '{sub_op_dict['anchor']}' in transcript.")
                        ids = [w["word_id"] for w in groups[0]]
                        working_tl = add_caption(working_tl, sub_op_dict["caption"], ids)
                        compound_ops.append({"type": "add_caption", "text": sub_op_dict["caption"], "word_ids": ids})
                    elif sub_op == "speed":
                        working_tl = speed_current(working_tl, sub_op_dict["start"], sub_op_dict["end"], sub_op_dict["speed"])
                        compound_ops.append({"type": "speed", "factor": sub_op_dict["speed"]})
                    elif sub_op == "caption_color":
                        working_tl = update_caption_style(working_tl, color=sub_op_dict["color"])
                        compound_ops.append({"type": "caption_color", "color": sub_op_dict["color"]})
                    else:
                        raise EngineError("UNSUPPORTED_OPERATION", f"Operation '{sub_op}' inside compound command is not supported.")
                
                before = clone(tl)
                session["timeline"] = _save_edit(before, working_tl, instruction)
                session["last_success_signature"] = signature
                return self._applied(session, compound_ops, "All compound operations applied atomically.", before=duration(before), started=start_time)

            before = clone(tl)
            operations = []
            label = instruction

            if op == "cut":
                after = cut_current(tl, parsed["start"], parsed["end"])
                operations = [{"type": "cut", "current_start": parsed["start"], "current_end": parsed["end"], "time_policy": "current_timeline"}]
            
            elif op == "keep":
                after = keep_current(tl, parsed["start"], parsed["end"])
                operations = [{"type": "keep", "current_start": parsed["start"], "current_end": parsed["end"], "time_policy": "current_timeline"}]
            
            elif op == "speed":
                after = speed_current(tl, parsed["start"], parsed["end"], parsed["speed"])
                operations = [{"type": "speed", "start": parsed["start"], "end": parsed["end"], "factor": parsed["speed"], "time_policy": "current_timeline", "overlap_rule": "newest speed instruction overrides the selected visible interval"}]
            
            elif op == "reorder":
                after = reorder_current(tl, parsed["start"], parsed["end"], parsed["target"])
                operations = [{"type": "reorder", "start": parsed["start"], "end": parsed["end"], "insert_at": parsed["target"], "time_policy": "current_timeline"}]
            
            elif op == "caption":
                groups = _visible_word_groups(tl, words, parsed["anchor"])
                if not groups:
                    raise EngineError("ANCHOR_NOT_FOUND", "I could not find that exact phrase in the transcript.", details={"phrase": parsed["anchor"]})
                if len(groups) > 1:
                    raise EngineError("AMBIGUOUS_ANCHOR", "That phrase appears more than once. Please include a more specific phrase or timestamp.", details={"matches": [{"start": g[0]["start"], "end": g[-1]["end"]} for g in groups]})
                ids = [w["word_id"] for w in groups[0]]
                after = add_caption(tl, parsed["caption"], ids)
                operations = [{"type": "add_caption", "text": parsed["caption"], "word_ids": ids}]
            
            elif op == "caption_color":
                after = update_caption_style(tl, color=parsed["color"])
                operations = [{"type": "caption_color", "color": parsed["color"], "caption_ids": [c["caption_id"] for c in after["captions"]]}]

            elif op == "caption_resize":
                after = update_caption_style(tl, font_size_delta=8 if parsed["direction"] == "bigger" else -8)
                operations = [{"type": "caption_resize", "direction": parsed["direction"], "caption_ids": [c["caption_id"] for c in after["captions"]]}]

            elif op == "speaker_cut":
                spk = parsed["speaker"]
                known_speakers = set(w.get("speaker") for w in words if w.get("speaker") and w.get("speaker") != "unknown")
                if not known_speakers:
                    return self._clarify(
                        "Speaker identities are marked 'unknown' because speaker diarization was not performed. Which time range or specific phrase would you like to cut instead?",
                        [
                            {"id": 1, "label": "Specify time range to cut (e.g. 'Cut from 0:10 to 0:25')"},
                            {"id": 2, "label": "Specify phrase to remove (e.g. 'Remove the part about...')"}
                        ],
                        tl,
                        "No destructive cut made before clarification."
                    )
                spk_words = [w for w in words if w.get("speaker") == spk and word_positions(tl, words).get(w["word_id"])]
                if not spk_words:
                    raise EngineError("NO_SPEAKER_WORDS", f"No words found for speaker '{spk}'. Known speakers: {sorted(list(known_speakers))}")
                after = _remove_source_ranges(tl, [(w["start"], w["end"]) for w in spk_words])
                operations = [{"type": "speaker_cut", "speaker": spk, "word_ids": [w["word_id"] for w in spk_words]}]

            elif op == "cut_after_phrase":
                groups = _visible_word_groups(tl, words, parsed["phrase"])
                if not groups:
                    raise EngineError("NO_MATCHES_FOUND", f"Could not find phrase '{parsed['phrase']}' in transcript.")
                if len(groups) > 1:
                    opts = [{"id": i + 1, "label": f"Occurrence {i + 1} at {g[-1]['end']:.2f}s"} for i, g in enumerate(groups)]
                    opts.append({"id": len(groups) + 1, "label": f"The last occurrence (at {groups[-1][-1]['end']:.2f}s)"})
                    session["pending"] = {
                        "question": f"'{parsed['phrase']}' occurs {len(groups)} times. After which occurrence should I cut everything?",
                        "options": opts,
                        "groups": groups,
                        "cut_after": True,
                        "phrase": parsed["phrase"]
                    }
                    return self._clarify(session["pending"]["question"], opts, tl, "No destructive cut made before clarification.")
                pos = word_positions(tl, words)
                ranges = pos.get(groups[0][-1]["word_id"], [])
                if not ranges:
                    raise EngineError("PHRASE_NOT_VISIBLE", "Phrase is not visible in current timeline.")
                current_cut_point = ranges[-1][1]
                after = cut_current(tl, current_cut_point, duration(tl))
                operations = [{"type": "cut_after_phrase", "phrase": parsed["phrase"], "from_time_s": current_cut_point}]

            elif op == "semantic_cut":
                groups = _visible_word_groups(tl, words, parsed["query"])
                if not groups:
                    raise EngineError("NO_MATCHES_FOUND", f"No transcript matches found for '{parsed['query']}'.")
                if len(groups) > 1:
                    opts = [{"id": i + 1, "label": f"Occurrence {i+1}: {g[0]['start']:.2f}s–{g[-1]['end']:.2f}s", "start_s": g[0]["start"], "end_s": g[-1]["end"]} for i, g in enumerate(groups)]
                    session["pending"] = {"question": f"I found {len(groups)} possible matches for '{parsed['query']}'. Which one should I remove, or should I remove all?", "options": opts, "groups": groups}
                    return self._clarify(session["pending"]["question"], opts, tl, "No destructive edit was made.")
                after = _remove_source_ranges(tl, [(groups[0][0]["start"], groups[0][-1]["end"])])
                operations = [{"type": "semantic_cut", "query": parsed["query"], "word_ids": [w["word_id"] for w in groups[0]]}]

            elif op == "word_effect":
                groups = _visible_word_groups(tl, words, parsed["word"])
                if not groups:
                    raise EngineError("WORD_NOT_FOUND", f"The word '{parsed['word']}' was not found in the transcript.")
                if parsed["effect"] in {"bleep", "mute"} and any(float(w.get("confidence", 1.0)) < 0.80 for g in groups for w in g):
                    low_words = [w for g in groups for w in g if float(w.get("confidence", 1.0)) < 0.80]
                    session["pending"] = {
                        "question": f"The transcript confidence for '{parsed['word']}' is low ({min(float(w.get('confidence', 1.0)) for w in low_words):.2f}). Confirm the {parsed['effect']}, or cancel by giving a different instruction?",
                        "options": [{"id": 1, "label": f"Confirm {parsed['effect']}"}],
                        "groups": [groups[0]],
                        "effect": parsed["effect"],
                        "needs_confirm": True
                    }
                    return self._clarify(session["pending"]["question"], session["pending"]["options"], tl, f"No {parsed['effect']} was applied because the word timing is low-confidence.")
                if len(groups) > 1:
                    opts = [{"id": i + 1, "label": f"{g[0].get('text', g[0].get('word',''))} at {g[0]['start']:.2f}s"} for i, g in enumerate(groups)]
                    session["pending"] = {"question": f"'{parsed['word']}' occurs {len(groups)} times. Which occurrence should I {parsed['effect']}?", "options": opts, "groups": groups, "effect": parsed["effect"]}
                    return self._clarify(session["pending"]["question"], opts, tl, "No word effect was added.")
                ids = [w["word_id"] for w in groups[0]]
                after = add_effect(tl, ids, parsed["effect"])
                operations = [{"type": parsed["effect"], "word_ids": ids}]

            elif op == "auto_caption":
                if not words:
                    raise EngineError("TRANSCRIPT_REQUIRED", "A transcript is needed before automatic captions can be added.")
                groups = []
                cur = []
                for w in words:
                    if not any(word_positions(tl, words).get(w["word_id"], [])):
                        continue
                    w_text = w.get("text", w.get("word", ""))
                    if cur and (w["start"] - cur[-1]["end"] > 0.65 or re.search(r"[.!?]$", cur[-1].get("text", cur[-1].get("word", "")))):
                        groups.append(cur)
                        cur = []
                    cur.append(w)
                    if len(cur) >= 7:
                        groups.append(cur)
                        cur = []
                if cur:
                    groups.append(cur)
                after = clone(tl)
                for g in groups:
                    after = add_caption(after, " ".join(x.get("text", x.get("word", "")) for x in g), [x["word_id"] for x in g])
                operations = [{"type": "auto_caption", "captions_added": len(groups)}]

            elif op == "remove_fillers":
                selected = [words[i] for i in range(len(words)) if _word_is_filler(words, i) and word_positions(tl, words).get(words[i]["word_id"])]
                if not selected:
                    raise EngineError("NO_FILLERS_FOUND", "No filler words were detected in the currently visible content.")
                after = _remove_source_ranges(tl, [(w["start"], w["end"]) for w in selected])
                operations = [{"type": "remove_fillers", "word_ids": [w["word_id"] for w in selected]}]

            elif op == "remove_silence":
                threshold = parsed["threshold"]
                if threshold <= 0 or threshold > 10:
                    raise EngineError("INVALID_SILENCE_THRESHOLD", "Silence threshold must be greater than 0 and at most 10 seconds.")
                gaps = []
                for a, b in zip(words, words[1:]):
                    gap = b["start"] - a["end"]
                    if gap > threshold:
                        gaps.append((a["end"] + 0.08, b["start"] - 0.08))
                if not gaps:
                    raise EngineError("NO_LONG_SILENCES", "No silence gaps exceeded the requested threshold.")
                after = _remove_source_ranges(tl, gaps)
                operations = [{"type": "remove_silence", "threshold_s": threshold, "ranges": gaps, "snap_pad_s": 0.08}]

            elif op == "restore_intro":
                end = min(30.0, tl["source_duration_s"])
                cover = sorted((s["source_start"], s["source_end"]) for s in tl["segments"] if s["source_start"] < end)
                missing = []
                cursor = 0.0
                for a, b in cover:
                    if a > cursor + 1e-7:
                        missing.append((cursor, min(a, end)))
                    cursor = max(cursor, b)
                if cursor < end - 1e-7:
                    missing.append((cursor, end))
                if not missing:
                    raise EngineError("INTRO_ALREADY_PRESENT", "The intro is already present in the timeline.")
                restored = [{"source_start": a, "source_end": b, "speed": 1.0} for a, b in missing]
                after = clone(tl)
                after["segments"] = [{"segment_id": f"seg_{i+1:04d}", **s} for i, s in enumerate(restored + tl["segments"])]
                operations = [{"type": "restore_intro", "source_ranges": missing}]

            elif op == "restore_edit":
                idx = parsed["edit_number"] - 1
                history = tl.get("history", [])
                if not 0 <= idx < len(history):
                    raise EngineError("HISTORY_ENTRY_NOT_FOUND", f"Edit number {parsed['edit_number']} does not exist in history (total: {len(history)}).")
                target = history[idx]
                restored = {k: v for k, v in target["timeline"].items()}
                restored["history"] = [*history[:idx], {"label": f"restore edit {parsed['edit_number']}", "timeline": _snapshot(tl)}]
                restored["redo"] = []
                after = restored
                operations = [{"type": "restore_edit", "edit_number": parsed["edit_number"], "label": target.get("label")}]

            elif op == "music":
                if not tl.get("music", {}).get("path"):
                    raise EngineError("MUSIC_ASSET_REQUIRED", "Upload a licensed music track first using the session music upload endpoint; then add it.")
                after = clone(tl)
                after["music"]["active"] = True
                after["music"]["duck_under_speech"] = True
                operations = [{"type": "add_background_music", "duck_under_speech": True}]

            else:
                raise EngineError("UNSUPPORTED_OPERATION", f"Operation '{op}' is not supported.")

            session["timeline"] = _save_edit(before, after, label)
            session["last_success_signature"] = signature
            return self._applied(session, operations, "Edit applied. Time values refer to the current timeline.", before=duration(before), started=start_time)
        
        except EngineError as e:
            return {
                "status": "rejected",
                "operations": [],
                "summary": {"message": e.message, "code": e.code, "details": e.details},
                "question": None,
                "options": [],
                "timeline_hash": timeline_hash(tl),
                "duration_s": round(duration(tl), 3)
            }

    def _clarify(self, question: str, options: list, tl: dict, message: str) -> dict:
        return {
            "status": "needs_clarification",
            "operations": [],
            "summary": {"message": message},
            "question": question,
            "options": options,
            "timeline_hash": timeline_hash(tl),
            "duration_s": round(duration(tl), 3)
        }

    def _applied(self, session: dict, operations: list, message: str, before: float | None = None, started: float | None = None) -> dict:
        tl = session["timeline"]
        after = duration(tl)
        result = {
            "status": "applied",
            "operations": operations,
            "summary": {
                "message": message,
                "before_duration_s": round(before if before is not None else after, 3),
                "after_duration_s": round(after, 3),
                "delta_s": round(after - (before if before is not None else after), 3),
                "time_policy": "current_timeline"
            },
            "question": None,
            "options": [],
            "timeline_hash": timeline_hash(tl),
            "duration_s": round(after, 3)
        }
        if started is not None:
            result["instruction_latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        return result
