from dataclasses import dataclass
import re

@dataclass
class SubtitleSegment:
    start: float
    end: float
    text: str

def format_timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def segments_to_srt(segments):
    blocks = []
    for index, segment in enumerate(segments, start=1):
        text = segment.text.strip()
        if not text:
            continue
        blocks.append("\n".join([
            str(index),
            f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}",
            text,
        ]))
    return "\n\n".join(blocks) + "\n"

def parse_srt(srt_text):
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    segments = []
    for block in blocks:
        lines = block.strip().splitlines()
        timestamp_line = next((line for line in lines if " --> " in line), None)
        if not timestamp_line:
            continue
        text_start = lines.index(timestamp_line) + 1
        start_raw, end_raw = timestamp_line.split(" --> ", 1)

        def parse_timestamp(value):
            value = value.replace(",", ".")
            h, m, s = value.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)

        segments.append(SubtitleSegment(
            start=parse_timestamp(start_raw),
            end=parse_timestamp(end_raw),
            text="\n".join(lines[text_start:]).strip(),
        ))
    return segments
