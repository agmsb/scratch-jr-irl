"""scratch-jr-irl, Step 1: Python backend + thin webpage.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000 in a browser.

All program logic lives in blocks.py. The webpage only taps blocks,
calls /api/expand, and animates the returned steps. No camera in Step 1.
Scanner (Step 3) will add POST /api/scan using OpenCV ArUco.
"""

from flask import Flask, jsonify, render_template, request

from blocks import BLOCKS, SAY_TEXT, expand_program

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


if __name__ == "__main__":
    # Localhost only. Project this laptop screen in class via HDMI.
    app.run(host="127.0.0.1", port=5000, debug=True)
