# scratch-jr-irl — Step 1

Python backend + thin webpage. Tap blocks, press GO, watch the cat run them.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000

## What Step 1 does

- Tap GO, Walk, Jump, Spin, Talk, AGAIN to build a program.
- AGAIN goes last and repeats all actions before it (default ×3, tap the AGAIN block to change to ×2 / ×3 / ×4).
- Talk uses the preset text “Hi, we’re Utopia!” — change `SAY_TEXT` in `blocks.py` before a lesson, not during it.
- Press GO to run. The currently running step is highlighted. Press Stop to reset the cat.
- Warnings from the backend show above the stage, e.g. AGAIN not last, or too many blocks.

## What Step 1 does not do

No camera, no scanning, no ArUco yet. That is Step 3. This step proves
the program logic (in `blocks.py`) and the player before any camera work.

## Files

- `app.py` — Flask app, serves the page and `/api/expand`
- `blocks.py` — block definitions, AGAIN semantics, validation, expansion
- `templates/index.html` — the page
- `static/app.js` — thin frontend: tap blocks, call the API, animate steps
- `static/style.css` — big, projector-readable buttons
