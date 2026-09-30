# Aplikacja Generowanie Napisów

## Wersje

- **V1** — upload i wyświetlenie wideo.
- **V2** — wyodrębnienie audio przez pydub + FFmpeg i `st.audio`.
- **V3** — speech-to-text przez OpenAI i wyświetlenie transkrypcji.
- **V4** — edycja transkrypcji w `st.text_area`.
- **V5** — segmenty z timestampami → SRT → edycja → pobranie SRT → wideo z napisami.

## Struktura

```text
aplikacja_generowanie_napisow/
├── app.py
├── requirements.txt
├── packages.txt
├── runtime.txt
├── .env.example
├── .gitignore
├── .streamlit/config.toml
├── v1/app.py
├── v2/app.py
├── v3/app.py
├── v4/app.py
└── v5/
    ├── app.py
    └── subtitle_utils.py
```

Celowo nie używam tutaj katalogu `src`, żeby repo było proste do uruchomienia na Streamlit Community Cloud.

## Streamlit Secrets

W **Manage app → Settings → Secrets**:

```toml
OPENAI_API_KEY = "..."
OPENAI_TRANSCRIPTION_MODEL = "whisper-1"
```

Kod najpierw sprawdza Secrets, a następnie lokalne zmienne środowiskowe.

## Lokalnie

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
streamlit run v5/app.py
```

FFmpeg jest instalowany na Streamlit Cloud przez `packages.txt`.

## Streamlit Cloud

Dla wersji V5 ustaw **Main file path** na:

```text
v5/app.py
```

Nie musisz zmieniać kodu.

## Dlaczego V5 używa timestampów?

Sam tekst transkrypcji nie wystarcza do zsynchronizowania napisów z filmem. V5 pobiera segmenty zawierające:

```text
start
end
text
```

i zamienia je na standardowy SRT:

```text
1
00:00:01,000 --> 00:00:03,500
Pierwszy napis.

2
00:00:03,500 --> 00:00:06,200
Drugi napis.
```

Streamlit obsługuje SRT/VTT bezpośrednio przez parametr `subtitles` w `st.video`.

## Limit pliku

`st.file_uploader` ma domyślnie limit 200 MB. W projekcie ustawiono 500 MB w `.streamlit/config.toml`.

Duże pliki wideo mogą jednak nadal być ograniczone przez pamięć, czas przetwarzania i limit usługi.

## Dalszy rozwój

- wybór języka,
- automatyczne wykrywanie języka,
- tłumaczenie napisów,
- VTT,
- poprawa interpunkcji przez LLM,
- speaker diarization,
- wypalanie napisów w filmie przez FFmpeg,
- object storage dla dużych plików.
