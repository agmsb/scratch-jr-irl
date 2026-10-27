"""scratch-jr-irl, Steps 1 + 3: Python backend + thin webpage.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000 in a browser.

All program logic lives in blocks.py. The webpage only taps blocks,
calls /api/expand, and animates the returned steps.
Scanner (Step 3) adds POST /api/scan using OpenCV ArUco: upload one
photo of physical cards, get back the detected program for the
confirm screen, then run it with /api/expand as usual.
"""

from flask import Flask, jsonify, render_template, request

from blocks import BLOCKS, SAY_TEXT, expand_program
from scanner import scan_image_bytes

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/blocks")
def api_blocks():
    return jsonify({"blocks": list(BLOCKS.values()), "say_text": SAY_TEXT})


@app.post("/api/expand")
def api_expand():
    data = request.get_json(silent=True) or {}
    result = expand_program(data.get("program", []), say_text=data.get("say_text"))
    return jsonify(result)


@app.post("/api/scan")
def api_scan():
    """Scan one uploaded photo. Field name: 'photo' (multipart file)."""
    photo = request.files.get("photo")
    if photo is None:
        return jsonify({"program": [], "detections": [], "warnings": ["No photo uploaded."], "hard_error": True}), 400
    result = scan_image_bytes(photo.read())
    # Also run the normal validation, so the confirm screen shows the
    # same warnings as a hand-built program (AGAIN not last, etc.).
    expanded = expand_program(result["program"])
    result["expanded"] = expanded
    result["warnings"] = result["warnings"] + expanded["warnings"]
    return jsonify(result)


if __name__ == "__main__":
    # Localhost only. Project this laptop screen in class via HDMI.
    app.run(host="127.0.0.1", port=5000, debug=True)
