# scratch-jr-irl — Steps 1 + 3

Python backend + thin webpage. Tap blocks, press GO, watch the cat run them.
Or lay physical cards in a row, scan one photo, check the program, then GO.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000

## Step 1: manual player

- Tap GO, Walk, Jump, Spin, Talk, AGAIN to build a program.
- AGAIN goes last and repeats all actions before it (default ×3, tap the AGAIN block to change to ×2 / ×3 / ×4).
- Talk uses the preset text “Hi, we’re Utopia!” — change `SAY_TEXT` in `blocks.py` before a lesson, not during it.
- Press GO to run. The currently running step is highlighted. Press Stop to reset the cat.

## Step 3: scanner

1. Generate cards:
   ```bash
   python cards/generate_cards.py
   ```
   Print `cards/*.png` at 100% on matte cardstock, not glossy. Check with a ruler: the black-and-white marker square should be at least 2.0 inches on a side.
2. Lay cards in one row, left to right, on a white mat with a taped guide line. Hands away for the photo.
3. In the app, under “Scan physical cards”, choose that photo and press “Scan photo”.
4. **Check the program before pressing GO.** That is the confirm screen. Edit it by tapping blocks to remove them, or tapping AGAIN to change its count. Nothing runs automatically from a scan.
5. Press GO to run the scanned program, exactly as with a hand-built one.

Card PNGs are generated locally and are not committed (binary files are excluded from snapshot pushes). Run the generator on any machine that needs a fresh set.

## Files

- `app.py` — Flask app, serves the page, `/api/expand`, `/api/scan`
- `blocks.py` — block definitions, AGAIN semantics, validation, expansion
- `scanner.py` — OpenCV ArUco detection, sorting, warnings, AGAIN + count handling
- `cards/generate_cards.py` — printable marker cards
- `templates/index.html` — the page
- `static/app.js` — thin frontend: tap blocks, scan photo, call the API, animate steps
- `static/style.css` — big, projector-readable buttons
