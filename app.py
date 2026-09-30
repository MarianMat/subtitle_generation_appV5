from __future__ import annotations
from io import BytesIO
from pathlib import Path
import os
import streamlit as st
from openai import OpenAI
from pydub import AudioSegment
from v5.subtitle_utils import SubtitleSegment, segments_to_srt

st.set_page_config(page_title="Aplikacja Generowanie Napisów V5", page_icon="🎬", layout="wide")

def get_secret(name, default=None):
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)

def extract_audio(video_bytes, extension):
    audio = AudioSegment.from_file(BytesIO(video_bytes), format=extension)
    out = BytesIO()
    audio.export(out, format="mp3", bitrate="64k")
    return out.getvalue()

def split_audio(audio_bytes, chunk_minutes=15):
    audio = AudioSegment.from_file(BytesIO(audio_bytes), format="mp3")
    chunk_ms = chunk_minutes * 60 * 1000
    result = []
    for start_ms in range(0, len(audio), chunk_ms):
        chunk = audio[start_ms:start_ms + chunk_ms]
        out = BytesIO()
        chunk.export(out, format="mp3", bitrate="64k")
        result.append((out.getvalue(), start_ms / 1000))
    return result

def transcribe_audio(client, audio_bytes, model, progress):
    chunks = split_audio(audio_bytes, 15)
    all_segments = []
    for i, (chunk_bytes, offset) in enumerate(chunks, 1):
        progress.progress((i-1)/len(chunks), text=f"Transkrypcja części {i}/{len(chunks)}...")
        audio_file = BytesIO(chunk_bytes)
        audio_file.name = f"audio_part_{i}.mp3"
        response = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
        for item in (getattr(response, "segments", None) or []):
            text = str(getattr(item, "text", "")).strip()
            if text:
                start = float(getattr(item, "start", 0.0)) + offset
                end = float(getattr(item, "end", start)) + offset
                all_segments.append(SubtitleSegment(start, end, text))
    progress.progress(1.0, text="Transkrypcja zakończona.")
    return all_segments

st.title("🎬 Aplikacja Generowanie Napisów — V5")
st.write("Wgraj film → wyodrębnij audio → wygeneruj timestampy → edytuj SRT → pobierz napisy.")

uploaded_video = st.file_uploader("Wybierz plik wideo", type=["mp4", "mov", "m4v", "webm", "avi"])

if uploaded_video:
    video_bytes = uploaded_video.getvalue()
    extension = Path(uploaded_video.name).suffix.lower().lstrip(".")
    if extension == "m4v": extension = "mp4"
    mime_type = uploaded_video.type or "video/mp4"

    st.subheader("1. Film")
    st.video(video_bytes, format=mime_type)

    st.subheader("2. Audio")
    if st.button("🎧 Wyodrębnij audio"):
        try:
            with st.spinner("Wyodrębniam audio..."):
                st.session_state["audio_bytes"] = extract_audio(video_bytes, extension)
            size = len(st.session_state["audio_bytes"]) / (1024*1024)
            st.success(f"Audio gotowe: {size:.1f} MB")
        except Exception as exc:
            st.error(f"Nie udało się wyodrębnić audio: {exc}")

    audio_bytes = st.session_state.get("audio_bytes")
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3")
        st.subheader("3. Generowanie napisów")
        api_key = get_secret("OPENAI_API_KEY")
        model = get_secret("OPENAI_TRANSCRIPTION_MODEL", "whisper-1")
        if not api_key:
            st.error("Brak OPENAI_API_KEY. Dodaj go w Streamlit Cloud → Manage app → Settings → Secrets.")
        else:
            st.caption(f"Model: `{model}`. Timestampy segmentów wymagają modelu obsługującego timestamp_granularities.")
            if st.button("🚀 Generuj napisy", type="primary"):
                try:
                    progress = st.progress(0, text="Przygotowuję transkrypcję...")
                    segments = transcribe_audio(OpenAI(api_key=api_key), audio_bytes, model, progress)
                    if not segments:
                        raise RuntimeError("API nie zwróciło segmentów z oznaczeniami czasu.")
                    st.session_state["srt_text"] = segments_to_srt(segments)
                    st.success(f"Gotowe. Utworzono {len(segments)} segmentów.")
                except Exception as exc:
                    st.error(f"Błąd podczas generowania napisów: {exc}")

    srt_text = st.session_state.get("srt_text")
    if srt_text:
        st.subheader("4. Edycja napisów SRT")
        st.info("Możesz edytować tekst i czasy. Zachowaj format linii czasu: HH:MM:SS,mmm --> HH:MM:SS,mmm")
        edited_srt = st.text_area("Treść pliku SRT", value=srt_text, height=500, key="srt_editor")
        st.session_state["srt_text"] = edited_srt

        st.subheader("5. Pobieranie")
        filename = Path(uploaded_video.name).stem + ".srt"
        st.download_button("⬇️ Pobierz plik SRT", data=edited_srt.encode("utf-8"), file_name=filename, mime="application/x-subrip", on_click="ignore")

        st.subheader("6. Podgląd filmu z napisami")
        try:
            st.video(video_bytes, format=mime_type, subtitles=edited_srt)
        except Exception as exc:
            st.warning(f"Podgląd z napisami nie jest dostępny, ale plik SRT można pobrać. {exc}")
else:
    st.info("👆 Wgraj film, aby rozpocząć.")
