import os
from io import BytesIO
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment

from v5.subtitle_utils import SubtitleSegment, segments_to_srt

load_dotenv()

st.set_page_config(page_title="Aplikacja Generowanie Napisów V5", page_icon="🎬", layout="wide")
st.title("🎬 Aplikacja Generowanie Napisów — V5")
st.caption("Wideo → audio → speech-to-text → edycja → SRT → wideo z napisami")

def get_secret(name, default=None):
    try:
        value = st.secrets.get(name)
        if value is not None:
            return value
    except Exception:
        pass
    return os.getenv(name, default)

def transcribe_audio(audio_bytes, api_key, model):
    client = OpenAI(api_key=api_key)
    audio_file = BytesIO(audio_bytes)
    audio_file.name = "audio.mp3"

    response = client.audio.transcriptions.create(
        model=model,
        file=audio_file,
        response_format="verbose_json",
        timestamp_granularities=["segment"],
    )

    segments = []
    for segment in response.segments:
        segments.append(SubtitleSegment(
            start=float(segment.start),
            end=float(segment.end),
            text=segment.text.strip(),
        ))
    return segments

api_key = get_secret("OPENAI_API_KEY")
model = get_secret("OPENAI_TRANSCRIPTION_MODEL", "whisper-1")

uploaded_video = st.file_uploader(
    "Wybierz plik wideo",
    type=["mp4", "mov", "m4v", "webm", "avi"],
)

if uploaded_video:
    video_bytes = uploaded_video.getvalue()

    st.markdown("## 1. Wideo wejściowe")
    st.video(video_bytes)

    extension = Path(uploaded_video.name).suffix.lower().lstrip(".") or "mp4"

    try:
        audio = AudioSegment.from_file(BytesIO(video_bytes), format=extension)
        audio_buffer = BytesIO()
        audio.export(audio_buffer, format="mp3")
        audio_bytes = audio_buffer.getvalue()

        with st.expander("🔊 2. Wyodrębniony dźwięk"):
            st.audio(audio_bytes, format="audio/mp3")

        if st.button("📝 3. Wygeneruj napisy", type="primary"):
            if not api_key:
                st.error(
                    "Brak OPENAI_API_KEY. Dodaj go w Streamlit Cloud → "
                    "Manage app → Settings → Secrets."
                )
                st.stop()

            with st.spinner(f"Transkrypcja przez {model}..."):
                try:
                    segments = transcribe_audio(audio_bytes, api_key, model)
                    st.session_state["srt_text"] = segments_to_srt(segments)
                except Exception as exc:
                    st.error("Nie udało się wygenerować napisów.")
                    st.exception(exc)

        if "srt_text" in st.session_state:
            st.markdown("## 4. Edycja napisów")

            edited_srt = st.text_area(
                "Edytuj tekst oraz znaczniki czasu w formacie SRT.",
                value=st.session_state["srt_text"],
                height=500,
                key="srt_editor",
            )
            st.session_state["srt_text"] = edited_srt

            col1, col2 = st.columns(2)

            with col1:
                if st.button("▶️ Pokaż wideo z napisami", type="primary"):
                    st.session_state["show_subtitles"] = True

            with col2:
                st.download_button(
                    "⬇️ Pobierz plik SRT",
                    data=edited_srt.encode("utf-8"),
                    file_name=Path(uploaded_video.name).stem + ".srt",
                    mime="application/x-subrip",
                    on_click="ignore",
                )

            if st.session_state.get("show_subtitles", False):
                st.markdown("## 5. Wideo z napisami")
                mime_type = uploaded_video.type or "video/mp4"
                st.video(
                    video_bytes,
                    format=mime_type,
                    subtitles=edited_srt,
                )
                st.success("Napisy są przekazane jako osobna ścieżka napisów.")
    except Exception as exc:
        st.error("Wystąpił błąd podczas wyodrębniania dźwięku z wideo.")
        st.exception(exc)
