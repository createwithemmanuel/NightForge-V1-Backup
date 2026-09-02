# NightForge V1

A lightweight web-based cinematic clip maker for sci-fi and horror scenes.

## What V1 does

Upload one still image and render a short 720p/24fps MP4 with:
- gentle zoom
- horizontal pan
- optional light flicker
- optional dark/foggy mood
- optional subtle camera shake

It intentionally does **not** run an AI video model.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Make sure FFmpeg is installed, then:

```bash
python app.py
```

Open the local address shown by Flask.

## Deploy to Render

1. Put this folder in a GitHub repository.
2. Connect the repository to Render.
3. Render can use `render.yaml` to configure the service.
4. The first build installs FFmpeg.
5. The free service is designed for small tests; it is not intended for heavy AI workloads.

## Important

The server filesystem is temporary on many free hosting setups. Download generated clips promptly and do not treat the server as permanent video storage.
