import os
import uuid
import subprocess
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOADS = os.path.join(BASE, "uploads")
OUTPUTS = os.path.join(BASE, "outputs")
os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(OUTPUTS, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nightforge-dev-key")
MAX_UPLOAD_MB = 8
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

ALLOWED = {".jpg", ".jpeg", ".png", ".webp"}

def make_clip(image_path, output_path, motion="zoom", duration=10, fps=24, fog=False, flicker=False, shake=False):
    # Render directly with FFmpeg's zoom/pan filters. This avoids storing thousands
    # of temporary frames and is intentionally lightweight for small cloud instances.
    duration = max(1, min(int(duration), 10))
    fps = 24
    vf = []

    # Work at 720p. A larger source is scaled/cropped; a smaller source is padded.
    if motion == "left":
        vf.append("scale=1280:-2,crop=1280:720:(iw-1280)*t/{0}:0".format(duration))
    elif motion == "right":
        vf.append("scale=1280:-2,crop=1280:720:(iw-1280)*(1-t/{0}):0".format(duration))
    else:
        # Gentle zoom, centered.
        vf.append("scale=1280:-2")
        vf.append("zoompan=z='min(zoom+0.0008,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=24")

    if shake:
        vf.append("crop=iw-8:ih-8:4+2*sin(18*t):4+2*cos(15*t)")

    if flicker:
        vf.append("eq=brightness='0.035*sin(9*t)+0.01*sin(31*t)'")

    if fog:
        # Very subtle temporal brightness variation rather than a heavy particle simulation.
        vf.append("eq=contrast=0.97:saturation=0.92")

    vf_str = ",".join(vf)

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", image_path,
        "-vf", vf_str,
        "-t", str(duration),
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an", output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        image = request.files.get("image")
        if not image or not image.filename:
            flash("Choose an image first.")
            return redirect(url_for("index"))

        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in ALLOWED:
            flash("Use JPG, JPEG, PNG, or WEBP.")
            return redirect(url_for("index"))

        job = uuid.uuid4().hex[:10]
        input_path = os.path.join(UPLOADS, job + ext)
        output_path = os.path.join(OUTPUTS, "nightforge_" + job + ".mp4")
        image.save(input_path)

        motion = request.form.get("motion", "zoom")
        fog = request.form.get("fog") == "on"
        flicker = request.form.get("flicker") == "on"
        shake = request.form.get("shake") == "on"

        try:
            make_clip(input_path, output_path, motion=motion, fog=fog, flicker=flicker, shake=shake)
            os.remove(input_path)
            return send_file(output_path, as_attachment=True, download_name="nightforge_clip.mp4")
        except Exception as exc:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            flash("Rendering failed. Check that FFmpeg is available on the server.")
            app.logger.exception(exc)
            return redirect(url_for("index"))

    return render_template("index.html")

@app.errorhandler(413)
def too_large(_):
    flash("Image is too large. Keep it under 8 MB.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
