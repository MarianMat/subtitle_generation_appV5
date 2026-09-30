from dataclasses import dataclass
import re

@dataclass
class SubtitleSegment:
    start: float
    end: float
    text: str

def format_timestamp(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3600000)
    minutes, rem = divmod(rem, 60000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def segments_to_srt(segments: list[SubtitleSegment]) -> str:
    blocks = []
    number = 1
    for s in segments:
        text = s.text.strip()
        if not text:
            continue
        blocks.append(f"{number}\n{format_timestamp(s.start)} --> {format_timestamp(s.end)}\n{text}\n")
        number += 1
    return "\n".join(blocks)

def parse_srt(srt_text: str) -> list[SubtitleSegment]:
    pattern = re.compile(r"(?ms)^\s*\d+\s*\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n(.*?)(?=\n\s*\n|\Z)")
    def t(v):
        h, m, rest = v.split(":"); sec, ms = rest.split(",")
        return int(h)*3600 + int(m)*60 + int(sec) + int(ms)/1000
    return [SubtitleSegment(t(a), t(b), txt.strip()) for a,b,txt in pattern.findall(srt_text) if txt.strip()]
