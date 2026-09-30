# Aplikacja Generowanie Napisów V5

Pipeline: video → audio → OpenAI Speech-to-Text → segmenty z timestampami → SRT → edycja → pobranie → podgląd filmu z napisami.

## Streamlit Cloud
Main file path: `v5/app.py`

Secrets:
```toml
OPENAI_API_KEY = "sk-..."
OPENAI_TRANSCRIPTION_MODEL = "whisper-1"
```

## Dlaczego whisper-1?
V5 potrzebuje segmentowych timestampów. OpenAI dokumentuje `whisper-1` z `verbose_json` i `timestamp_granularities=["segment"]`.

## Limit audio
OpenAI Transcriptions API ma limit 25 MB na pojedynczy plik audio. V5 eksportuje MP3 64 kbps i dzieli długie audio na 15-minutowe części, a potem dodaje offset czasu do segmentów.

## Python 3.14
`audioop-lts` jest dodany jako zależność dla PyDub na Pythonie 3.13+.
