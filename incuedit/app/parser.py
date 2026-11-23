from __future__ import annotations
import re
from app.errors import EngineError

SYNONYMS = {
    "pricing": ["pricing", "price", "cost", "costs", "expensive", "budget", "rates", "fee", "fees"],
    "cost": ["cost", "costs", "pricing", "price", "budget", "expense", "expenses"],
    "intro": ["intro", "introduction", "welcome", "beginning", "start"],
    "outro": ["outro", "conclusion", "ending", "goodbye", "thanks"],
    "thanks": ["thanks", "thank you", "thank", "thx"]
}

WORD_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60
}

def normalize_words(text: str) -> str:
    s = text
    for word, num in WORD_NUMBERS.items():
        s = re.sub(rf"\b{word}\b", str(num), s, flags=re.I)
    return s

def parse_time(value: str, duration_s: float | None = None) -> float:
    s = normalize_words(value.strip().lower())
    if s.startswith("from "):
        s = s[5:].strip()
    if s.startswith("at "):
        s = s[3:].strip()
    if s in {"beginning", "start", "the beginning"}:
        return 0.0
    if s in {"end", "the end"} and duration_s is not None:
        return duration_s
    if (s.startswith("last ") or s.startswith("the last ")) and duration_s is not None:
        m = re.search(r"last\s+(\d+(?:\.\d+)?)\s*(seconds?|secs?|s)", s)
        if m:
            return max(0.0, duration_s - float(m.group(1)))
    m = re.fullmatch(r"(\d+):(\d{1,2})(?::(\d{1,2}))?", s)
    if m:
        nums = [int(x) for x in m.groups() if x is not None]
        if len(nums) == 2:
            return nums[0] * 60 + nums[1]
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    m = re.search(r"(\d+(?:\.\d+)?)\s*(seconds?|secs?|s)\b", s)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*(minutes?|mins?|m)\b", s)
    if m:
        return float(m.group(1)) * 60
    if "a minute twenty" in s or "one minute twenty" in s or "a minute 20" in s or "1 minute 20" in s:
        return 80.0
    if "half a minute" in s:
        return 30.0
    if re.search(r"(?<!half\s)\b(?:a|1|one)\s+minute\b", s):
        return 60.0
    # Match standalone integer
    if s.isdigit():
        return float(s)
    raise EngineError("UNPARSEABLE_TIME", f"Could not understand the time value: {value}")

def tokens(text: str) -> list[str]:
    return re.findall(r"[\w']+", text.lower())

def find_word_matches(words: list[dict], phrase: str, timeline=None) -> list[list[dict]]:
    target = tokens(phrase)
    if not target:
        return []
    candidates = [target]
    if len(target) == 1 and target[0] in SYNONYMS:
        candidates = [[x] for x in SYNONYMS[target[0]]]
    wtokens = [tokens(w.get("text", w.get("word", ""))) for w in words]
    result = []
    seen = set()
    for candidate in candidates:
        for i in range(len(words) - len(candidate) + 1):
            joined = []
            for j in range(i, min(len(words), i + len(candidate))):
                joined.extend(wtokens[j])
            if joined[:len(candidate)] == candidate:
                group = words[i:i + len(candidate)]
                key = tuple(x["word_id"] for x in group)
                if key not in seen:
                    seen.add(key)
                    result.append(group)
    return sorted(result, key=lambda g: g[0]["start"])

def parse_single_instruction(text: str, duration_s: float | None = None) -> dict:
    s = text.strip()
    low = s.lower()
    
    if low in {"undo", "undo last edit"}:
        return {"op": "undo"}
    if low in {"redo", "redo last edit"}:
        return {"op": "redo"}
    if low in {"render", "export", "render video"}:
        return {"op": "render"}
    if low in {"auto-caption", "auto caption", "add captions to the whole video", "caption the whole video", "auto-caption the whole video", "auto caption the whole video", "add captions to the complete video"}:
        return {"op": "auto_caption"}
    if "remove filler" in low or "cut filler" in low or "remove ums" in low:
        return {"op": "remove_fillers"}
    if "remove silence" in low or "remove pauses" in low or "remove silences" in low:
        m = re.search(r"(?:longer than|over|above)\s+(\d+(?:\.\d+)?)\s*(?:seconds?|s)", low)
        return {"op": "remove_silence", "threshold": float(m.group(1)) if m else 1.0}
    if ("restore" in low and ("intro" in low or "beginning" in low)) or ("intro" in low and ("back" in low or "put" in low or "bring" in low)):
        return {"op": "restore_intro"}
    
    # Restore specific edit: "restore edit number 3", "restore edit 2"
    m = re.search(r"restore\s+(?:edit\s+(?:number\s+)?|snapshot\s+)(\d+)", low)
    if m:
        return {"op": "restore_edit", "edit_number": int(m.group(1))}

    # Vague instructions
    if "the boring part" in low or low in {"make it shorter", "cut the boring part", "the boring section"}:
        return {"op": "vague_instruction", "text": text}
    if low in {"make it bigger", "make it smaller"} and not any(w in low for w in ["caption", "text"]):
        return {"op": "vague_instruction", "text": text}

    # Speed instructions
    m = re.search(r"(?:speed up|speed|slow down)\s+(?:the\s+section\s+)?(?:from\s+)?(.+?)\s+to\s+(.+?)\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*x", low)
    if m:
        factor = float(m.group(3))
        return {
            "op": "speed",
            "start": parse_time(m.group(1), duration_s),
            "end": parse_time(m.group(2), duration_s),
            "speed": factor if "slow" not in low else 1 / factor
        }
    m = re.search(r"(?:speed up|slow down)\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*x", low)
    if m:
        factor = float(m.group(1))
        return {
            "op": "speed",
            "start": 0.0,
            "end": duration_s or 0.0,
            "speed": factor if "slow" not in low else 1 / factor
        }
    if low in {"make this section slower", "make it slower", "slow down this section"}:
        return {"op": "speed", "start": 0.0, "end": duration_s or 0.0, "speed": 0.5}

    # Caption color styling: "Make that caption red", "Set caption color to blue"
    m = re.search(r"(?:make|set)\s+(?:that\s+|the\s+)?caption\s+(?:color\s+(?:to\s+)?)?(red|green|blue|yellow|white|black|cyan|magenta|orange)", low)
    if m:
        return {"op": "caption_color", "color": m.group(1)}

    # Caption resizing: "Make that caption bigger", "Make caption smaller"
    m = re.search(r"(?:make|set)\s+(?:that\s+|the\s+)?caption\s+(bigger|larger|smaller)", low)
    if m:
        return {"op": "caption_resize", "direction": "smaller" if "smaller" in m.group(1) else "bigger"}

    # Cut relative to phrase: "Remove everything after I say thanks"
    m = re.search(r"(?:remove|cut|delete)\s+everything\s+after\s+(?:i\s+say\s+|saying\s+)?['\"]?([\w\s'-]+?)['\"]?$", low)
    if m:
        return {"op": "cut_after_phrase", "phrase": m.group(1).strip()}

    # Speaker cuts: "Remove speaker 2", "Remove what speaker 2 said", "remove everything the second speaker said about price"
    m_spk = re.search(r"(?:remove|cut|delete)\s+(?:everything\s+)?(?:what\s+)?(?:the\s+)?(?:from\s+)?(?:(first|second|third|1st|2nd|3rd)\s+speaker|speaker[_\s]+([0-9a-zA-Z]+))(?:\s+said)?(?:\s+about\s+([a-zA-Z0-9_\-\s]+))?", low)
    if m_spk:
        ord_spk, num_spk, topic = m_spk.group(1), m_spk.group(2), m_spk.group(3)
        spk_id = "speaker_1"
        if ord_spk:
            if "second" in ord_spk or "2nd" in ord_spk:
                spk_id = "speaker_2"
            elif "third" in ord_spk or "3rd" in ord_spk:
                spk_id = "speaker_3"
            else:
                spk_id = "speaker_1"
        elif num_spk:
            spk_id = f"speaker_{num_spk.strip().strip('_')}"
        topic_clean = topic.strip() if topic else None
        return {"op": "speaker_cut", "speaker": spk_id, "topic": topic_clean}

    # Time-based cuts
    m = re.search(r"(?:cut|remove|delete)\s+(?:the\s+)?(?:first\s+)?(.+?)\s*(?:-|to|through)\s*(.+)$", low)
    if m:
        return {"op": "cut", "start": parse_time(m.group(1), duration_s), "end": parse_time(m.group(2), duration_s)}
    m = re.search(r"(?:cut|remove|delete)\s+(?:the\s+)?first\s+(.+)$", low)
    if m:
        return {"op": "cut", "start": 0.0, "end": parse_time(m.group(1), duration_s)}
    m = re.search(r"(?:cut|remove|delete)\s+(?:the\s+)?last\s+(.+)$", low)
    if m and duration_s is not None:
        seconds = parse_time(m.group(1), duration_s)
        return {"op": "cut", "start": max(0.0, duration_s - seconds), "end": duration_s}

    # Reorder
    m = re.search(r"(?:move|reorder)\s+(?:the\s+)?section\s+from\s+(.+?)\s+to\s+(.+?)\s+(?:to|at)\s+(.+)$", low)
    if m:
        return {
            "op": "reorder",
            "start": parse_time(m.group(1), duration_s),
            "end": parse_time(m.group(2), duration_s),
            "target": parse_time(m.group(3), duration_s)
        }

    # Keep
    m = re.search(r"keep\s+(?:only\s+)?(?:the\s+)?(?:first\s+)?(.+?)\s*(?:to|until|through)\s*(.+)$", low)
    if m:
        return {"op": "keep", "start": parse_time(m.group(1), duration_s), "end": parse_time(m.group(2), duration_s)}
    m = re.search(r"keep\s+(?:only\s+)?(?:the\s+)?first\s+(.+)$", low)
    if m:
        return {"op": "keep", "start": 0.0, "end": parse_time(m.group(1), duration_s)}

    # Word effects
    m = re.search(r"(?:mute|bleep)\s+(?:the\s+)?(?:word\s+)?['\"]?([\w'-]+)['\"]?", low)
    if m:
        return {"op": "word_effect", "word": m.group(1), "effect": "mute" if low.startswith("mute") else "bleep"}

    # Captions
    m = re.search(r"add\s+(?:a\s+)?caption\s+['\"](.+?)['\"]\s+(?:when|on)\s+i\s+say\s+(.+)$", s, re.I)
    if m:
        return {"op": "caption", "caption": m.group(1), "anchor": m.group(2)}

    # Semantic cut
    m = re.search(r"(?:remove|cut|delete)\s+(?:the\s+)?(?:part|section)\s+about\s+(.+)$", low)
    if m:
        return {"op": "semantic_cut", "query": m.group(1).strip(" .?!")}

    # Background music
    m = re.search(r"add\s+(?:background\s+)?music(?:\s+and\s+(?:lower|duck)\s+it\s+while\s+i\s+speak)?(?:\s+from\s+(.+))?", low)
    if m:
        return {"op": "music", "source": m.group(1)}

    raise EngineError(
        "INSTRUCTION_NOT_UNDERSTOOD",
        "I could not map that request to a safe editing operation. Try a specific cut, caption, speed, mute, filler-removal, undo, or render instruction.",
        details={"instruction": text}
    )

def parse_instruction(text: str, duration_s: float | None = None) -> dict:
    raw = text.strip()
    # Support compound instructions linked with ' and '
    # e.g., "Cut the first 5 seconds and add a caption 'Hello' when I say welcome"
    # But do not split on 'and' inside quotes or ducking phrases
    if " and " in raw.lower() and not re.search(r"['\"].*and.*['\"]", raw, re.I) and "lower it while" not in raw.lower() and "duck" not in raw.lower():
        parts = [p.strip() for p in re.split(r"\s+and\s+", raw, flags=re.I) if p.strip()]
        if len(parts) > 1:
            try:
                sub_ops = [parse_single_instruction(p, duration_s) for p in parts]
                return {"op": "compound", "operations": sub_ops, "raw_parts": parts}
            except EngineError:
                pass # Fall back to single instruction parsing
                
    return parse_single_instruction(raw, duration_s)
