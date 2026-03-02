import io
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Tuple

from flask import Flask, jsonify, render_template, request
from PIL import Image, UnidentifiedImageError

MAX_SIZE_BYTES = 2 * 1024 * 1024 - 10 * 1024  # marge de securite (~10KB)
MIN_QUALITY = 25
START_QUALITY = 92
RESIZE_FACTOR = 0.9

app = Flask(__name__)


def getenv_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def compress_image_to_target(data: bytes, original_name: str) -> Tuple[bytes, str, str]:
    """Return (compressed_bytes, output_filename, mime_type)."""
    try:
        image = Image.open(io.BytesIO(data))
    except UnidentifiedImageError as exc:
        raise ValueError(f"{original_name}: format d'image non reconnu") from exc

    # Conversion JPEG pour une meilleure maitrise de la taille.
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    candidate = image
    quality = START_QUALITY
    output = io.BytesIO()

    while True:
        output.seek(0)
        output.truncate(0)
        candidate.save(output, format="JPEG", optimize=True, quality=quality)
        current_size = output.tell()

        if current_size <= MAX_SIZE_BYTES:
            compressed_name = f"{Path(original_name).stem}_compressed.jpg"
            return output.getvalue(), compressed_name, "image/jpeg"

        if quality > MIN_QUALITY:
            quality = max(MIN_QUALITY, quality - 7)
            continue

        width, height = candidate.size
        new_width = int(width * RESIZE_FACTOR)
        new_height = int(height * RESIZE_FACTOR)

        if new_width < 300 or new_height < 300:
            raise ValueError(
                f"{original_name}: impossible de passer sous 2Mo sans degrader excessivement"
            )

        candidate = candidate.resize((new_width, new_height), Image.Resampling.LANCZOS)
        quality = START_QUALITY


def send_email_with_attachments(files: list[tuple[bytes, str, str]], subject: str) -> None:
    smtp_host = getenv_required("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = getenv_required("SMTP_USER")
    smtp_password = getenv_required("SMTP_PASSWORD")
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    mail_from = getenv_required("MAIL_FROM")
    mail_to = getenv_required("MAIL_TO")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg.set_content(
        "Les images compressees (<2Mo) sont en piece jointe.\n"
        "Message envoye automatiquement depuis le service Raspberry Pi."
    )

    for content, filename, mime_type in files:
        maintype, subtype = mime_type.split("/", 1)
        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        if smtp_use_tls:
            server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/upload")
def upload():
    uploaded_files = request.files.getlist("files")

    if not uploaded_files:
        return jsonify({"error": "Aucun fichier recu"}), 400

    compressed_files = []
    results = []

    for item in uploaded_files:
        if not item.filename:
            continue
        raw = item.read()

        try:
            compressed, filename, mime_type = compress_image_to_target(raw, item.filename)
            compressed_files.append((compressed, filename, mime_type))
            results.append(
                {
                    "input": item.filename,
                    "output": filename,
                    "size_kb": round(len(compressed) / 1024, 1),
                }
            )
        except ValueError as err:
            return jsonify({"error": str(err)}), 400

    if not compressed_files:
        return jsonify({"error": "Aucune image valide traitee"}), 400

    send_email_with_attachments(compressed_files, "Photos compressees (<2Mo)")
    return jsonify({"ok": True, "files": results})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=False)
