"""Cache key for a voice line (tools/voice.py)."""
import hashlib
import json

DIRECTION_KEYS = ("emotion", "pace", "emphasis")


def voice_settings(c: dict) -> list:
    s = [c.get("refVoice"), c.get("exaggeration"), c.get("cfgWeight")]
    if c.get("engine"):  # non-Chatterbox engines: their own settings decide the sound
        s += [c["engine"], c.get("speaker"), c.get("style")]
    return s


def cache_key(line: dict, chars: dict, lang: str) -> str:
    """Same text + voice settings → same audio file, so edits only regenerate changed lines."""
    voices = list(chars.values()) if line["speaker"] == "all" else [chars[line["speaker"]]]
    key = [line["text"], [voice_settings(c) for c in voices]]
    if lang != "en":  # keep English keys unchanged so existing caches stay valid
        key.insert(0, lang)
    if any(line.get(k) for k in DIRECTION_KEYS):  # undirected lines keep their old keys
        key.append({k: line.get(k) for k in DIRECTION_KEYS})
    return hashlib.sha1(json.dumps(key).encode()).hexdigest()[:10]
