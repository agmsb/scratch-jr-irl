# Tangible ScratchJr MVP Spec — “Scan the Blocks, Run the Cat”

**Status:** Draft v1, Oct 26, 2026. Spec only — no app built yet.
**Stack decision, Oct 26, 2026:** Python backend + webpage (not JavaScript-first). Anthony is more familiar with Go/Python than JavaScript, and Python's OpenCV is the native path for ArUco. See §2.
**Purpose:** Let kids lay physical ScratchJr-style blocks in a row, scan them with a camera, see the same blocks appear on screen, then press GO and watch a cat run them.
**Lesson it serves:** The 20-minute “Program the Cat” lesson for Benjamin’s Utopia pre-K class at St. Thomas More (see `scratchjr-lesson-plan.md`). The official ScratchJr lesson stays the plan. This app is an optional add-on — it does **not** replace the lesson until it passes the acceptance tests in §11.
**Name it in class:** Call the on-screen player “Cat Player” or “Tangible Cat,” not ScratchJr. It uses the same 5 lesson blocks, but it is not the official ScratchJr app.

---

## 1. Goal and non-goals

### Goal
One reliable classroom moment: kids build a physical sequence, the camera reads it once, the screen shows the identical sequence, the cat performs it — including the bug, so the class can fix it.

### Non-goals for v1
- No live, continuous camera tracking. Scan-on-demand only (one photo per program).
- No full ScratchJr. No sprites, backgrounds, sounds library, saving/sharing, accounts, or free text.
- No nesting, no conditionals, no variables, no multi-character programs.
- No plug-in to the official ScratchJr app. There is no live external API for that. A .sjr export is a possible v2, not v1.
- No App Store release. This is a personal / classroom demo.

## 2. Recommended stack: Python backend + webpage

**v1: Python backend serving a thin webpage.**
- Backend: Python with Flask (requirements in `requirements.txt`). All program logic lives in Python — block definitions, AGAIN expansion, validation, and later ArUco scanning.
- Webpage: a single HTML page with CSS and a small amount of JavaScript. The JavaScript is deliberately thin: tap blocks to build a sequence, show the confirm screen, highlight the current block, and animate the cat on Canvas. It does not decide what a program means.
- API, Step 1: `POST /api/expand` — send the tapped sequence, get back the expanded execution steps (with AGAIN applied) plus any validation warnings. The page then plays those steps.
- API, Step 3 (scanner, not Step 1): `POST /api/scan` — send one photo, the backend runs OpenCV ArUco detection (`cv2.aruco`, DICT_4X4_50), sorts and validates, and returns blocks + warnings for the confirm screen.
- Run it from `localhost` on the laptop so webcam permission works in Step 3, and project the laptop screen to the classroom via HDMI.

Why Python backend first: Anthony is more familiar with Python than JavaScript, and Python's OpenCV is the native, well-documented path for ArUco — no OpenCV.js bundling. Go was considered and set aside for v1: GoCV bindings for ArUco are heavier to set up and less ergonomic for this job.

**v2 (only if v1 is a hit): iPad app.**
- Swift + AVFoundation + OpenCV ArUco bridged via Objective-C.
- Rear camera on a stand, or front camera with an Osmo-style reflector. Do not start here — the reflector, focus distance, and classroom lighting are the hard parts, and they are all avoided in v1.

## 3. Physical cards

### Print spec
- Matte cardstock, **not glossy** (glare kills detection).
- Card size: about 5 in wide × 4 in tall, printed at 100% scale. Test scale before cutting a full set.
- Front face, human-readable first: ScratchJr colour background, big icon, and one word (WALK, JUMP, SPIN, TALK, AGAIN, GO).
- ArUco marker in the bottom-right corner of the **same** face, at least 2.0 in square, with at least 0.25 in of white border around it. Kids should not have to flip cards to scan.
- One white mat for the table, with a taped horizontal guide line. Cards sit on the line, left to right.

### Dictionary and IDs
Use **DICT_4X4_50**. 4×4 markers detect more reliably at classroom distance than 6×6, and v1 needs very few IDs.

| Marker ID | Card | ScratchJr colour | Kid name |
|---:|---|---|---|
| 0 | GO (green flag) | Yellow | “GO button” |
| 1 | Walk / Move Right | Blue | “Walk” |
| 2 | Jump / Hop | Blue | “Jump” |
| 3 | Spin / Turn | Blue | “Spin” |
| 4 | Say | Purple | “Talk” |
| 5 | AGAIN (Repeat) | Orange | “AGAIN block” |
| 10 | Number ×2 | Orange / grey | “2 times” |
| 11 | Number ×3 | Orange / grey | “3 times” |
| 12 | Number ×4 | Orange / grey | “4 times” |

Print at least: GO ×1, Walk ×3, Jump ×2, Spin ×2, Say ×1, AGAIN ×1, ×2 / ×3 / ×4 ×1 each. Duplicates of Walk/Jump/Spin are expected. Duplicates of GO, Say, AGAIN, or a number tile are errors (see §6).

### Layout rules for v1 (say these out loud in class)
1. One row only, left to right, on the guide line.
2. GO first, if it is used.
3. AGAIN last, if it is used — optionally followed by one number tile.
4. Cards may touch, but markers must not overlap and must not be covered by hands in the photo.
5. If a card is upside down, the scan still reads it, but the confirm screen will flag it. Keep cards upright when possible.

## 4. Program semantics (v1, deliberately simple)

This is the most important design decision in the spec. Do not try to copy ScratchJr’s nested Repeat block in a linear row of cards.

- **Sequence:** Everything between GO and the end, in left-to-right order.
- **GO:** A trigger, not an action. If GO is missing, the confirm screen offers “Add GO at start” instead of failing.
- **Walk:** Cat moves right 90 px.
- **Jump:** Cat arcs up and lands in place.
- **Spin:** Cat rotates 360°.
- **Say:** Cat shows a speech bubble with the **preset** text for 2.5 seconds. v1 has no typing, no OCR, no speech input.
  - Default preset: “Hi, we’re Utopia!” — change this in settings before the lesson, not during it.
- **AGAIN:** Repeats **all** action blocks before it. It does not wrap a subset.
  - `GO Walk Jump AGAIN` = Walk, Jump, Walk, Jump.
  - `GO Walk Jump AGAIN ×3` = Walk, Jump, repeated 3 times total (not 3 extra times — say this explicitly in class).
  - No number tile after AGAIN = repeat ×3 by default, to keep the run short.
  - AGAIN in the middle of a sequence is a confirm-screen error: “AGAIN has to go last.” The teacher moves it, or removes it.
- **Maximum length:** 10 action blocks before AGAIN. Longer than that is unwatchable in a 20-minute lesson, and it hides the bug.
- **Stage edge:** If Walk would push the cat off the right edge, the cat stops at the edge and the run continues. This is a feature for the lesson: “he bumped into the wall — that’s the bug, how do we fix it?” Do not wrap, do not crash.

### Example programs
- `GO Walk Walk Jump Say` — the core lesson build.
- `GO Spin Walk` — the deliberate bug: he spins first, then walks. The cat did not mess up; the blocks did.
- `GO Walk Jump AGAIN ×3` — the loop finale, one GO press, three performances.

## 5. App flow (3 screens, no more)

### Screen 1 — Scan
- Big camera preview, big **SCAN** button, big **Build by hand** button (see §8).
- Instruction in kid words: “Put your blocks in a line, hands away, press SCAN.”
- On SCAN: capture one still, run detection, go to Screen 2. Never auto-rescan while hands are moving.

### Screen 2 — Confirm (this screen is the safety net)
Show the detected sequence as digital blocks, in ScratchJr colours, left to right, with:
- Position numbers under each block.
- Warnings, in plain language, for: missing GO, duplicate GO/AGAIN/number, AGAIN not last, unknown marker, card too rotated, cards not in one row.
- Teacher-only edits: tap a block to delete it, tap “Add GO at start,” tap a number tile to change ×2 / ×3 / ×4.
- Two big buttons: **Scan again** and **Looks right — GO**.
- Rule: never run a program straight from the camera without this screen. The confirm screen is what makes a misread a teachable moment instead of a classroom failure.

### Screen 3 — Run
- Top: the digital program, with the currently executing block highlighted.
- Middle: the stage, one cat, starting at the left.
- Bottom: **GO** (large), **Stop**, and **Back to blocks**.
- Timing (approximate, tune by feel): Walk 0.6 s, Jump 0.6 s, Spin 0.8 s, Say 2.5 s, 0.25 s pause between blocks.
- After the run: **Run again** and **Fix the blocks** (back to Screen 2, then Screen 1 if cards change).

## 6. Scanner algorithm

1. Capture a still at the highest webcam resolution available (aim for 1920 px wide).
2. Convert to grayscale, run ArUco detection with DICT_4X4_50.
3. For each detection, record: marker ID, centre (x, y), corner positions, and estimated rotation.
4. Drop detections with no ID match. Keep a list of unknown detections by position so Screen 2 can say “something in position 3 didn’t read.”
5. Sort by centre x, ascending. This is the program order.
6. Row check: if max centre y − min centre y is greater than about 1.5× a marker’s height, flag “cards are not in one row.”
7. Rotation check: if a marker is rotated more than ~45° from upright, flag it, but still accept the ID.
8. Duplicate check: GO, Say, AGAIN, and number tiles may appear at most once. Walk/Jump/Spin may repeat.
9. Map IDs to blocks using §3. Unknown IDs go to Screen 2 as an “unknown card” placeholder, never silently dropped.
10. If zero markers are found, stay on Screen 1 with a specific hint (“Move the camera closer / turn the light on / make sure the black-and-white squares are showing”), not a generic error.

Do not add pose estimation, 3D tracking, or hand tracking in v1. Centre-x sorting is enough for one row.

## 7. Player

- Logical stage: 960 × 540, scaled to the projected screen.
- Cat: a simple drawn cat or an emoji-style sprite in v1 — do not spend the weekend on art. The blocks are the lesson, not the cat.
- Execution is sequential with `await` per block. Highlight the current block on Screen 3 while it runs.
- Sound: off by default in v1. Optional “boing” for Jump only if it does not distract.
- Stop button must halt immediately and return the cat to its start position.

## 8. Manual fallback (required, not optional)

Screen 1 must always offer **Build by hand**: tap digital blocks in order to build the same sequence, then run it on Screen 3. This is:
- The backup if the camera, lighting, or printer fails in class.
- The fastest way to test the player without printing cards.
- The honest version of the lesson if the scan is not ready: the kids still build physically, the teacher mirrors it by hand, the cat still runs it.

If the camera path is not classroom-ready, use this fallback and do not pretend the scan worked.

## 9. Suggested file layout

```
scratch-jr-irl/
  app.py              # Flask app: serves the page, /api/expand (Step 1), /api/scan (Step 3)
  blocks.py           # Marker map (§3) + program semantics (§4) + validation + AGAIN expansion
  scanner.py          # Step 3 only: OpenCV ArUco detection, sorting, warnings (§6)
  requirements.txt    # Flask, opencv-python (scanner only, Step 3)
  templates/index.html # Screens 1–3, stage, confirm UI (thin JavaScript only)
  static/app.js       # Tap blocks, call /api/expand, highlight + animate steps
  static/style.css    # Big buttons, ScratchJr colours, projector-readable text
  cards/
    generate_cards.py # OpenCV: generate DICT_4X4_50 markers + card PDFs
    cards.pdf         # Print at 100%, matte cardstock
  README.md           # How to run locally, camera setup, print notes
  scratchjr-tangible-mvp-spec.md
```

No database, no login. Run it from `localhost` so the webcam permission works in Step 3.

## 10. Classroom kit checklist

- [ ] Laptop + charger + HDMI cable/adapter for the classroom screen
- [ ] Webcam on a tripod/gooseneck, aimed down at the table, 18–24 in from the cards (measure this at home)
- [ ] White mat + taped guide line
- [ ] Printed card set + 1 spare set
- [ ] Preset Say text set before the lesson
- [ ] Manual-fallback tested (Screen 1 → Build by hand → Run) with no camera at all
- [ ] A printed copy of the lesson’s block cards as the ultimate backup (already in the lesson plan)

## 11. Test plan and acceptance criteria — do not take it to class until these pass

Home tests, in classroom-like light (not just a bright desk lamp):
1. Each card alone, 5 trials each — must read correctly every time at 18–24 in.
2. `GO Walk Walk Jump Say` — 10 trials, cards shuffled and re-laid each time.
3. `GO Spin Walk` (bug case) — cat must spin first, every time.
4. `GO Walk Jump AGAIN ×3` — must run Walk/Jump 3 times total, not 4, not 2.
5. Missing GO — confirm screen must offer to add it.
6. AGAIN in the middle — confirm screen must flag it.
7. One marker covered by a hand — scan must not silently run a shorter program; it must flag the unread position.
8. Glare / dim room — if it fails, change paper/lighting/distance, not the lesson plan.
9. Full run-through with Benjamin (or another 5-year-old) placing the cards — watch for rotation, overlapping, and hands in the photo.
10. Projector test: confirm screen and stage must be readable from the back of a classroom.

**Classroom-ready bar (estimate, not a guarantee):** at least 9/10 clean scans on tests 2–4, scan-to-confirm under ~5 seconds, and manual fallback working with the camera unplugged. If it misses that bar, use the lesson as planned and keep building — do not debug live in front of pre-K.

## 12. Risks and kill criteria

- **Camera distance/focus:** Laptop webcams are soft at close range. If markers under 2 in do not read reliably, print larger cards or move to a better webcam — do not shrink the markers to make the cards prettier.
- **Lighting:** Overhead classroom fluorescents + glossy paper = glare. Matte paper and a white mat matter more than a better algorithm.
- **Scope creep:** The moment you add nested loops, free-text Say, or live tracking, this stops being a weekend MVP. Those are v2, after the lesson.
- **Kill criterion:** If, after the home tests, scanning is still flaky, or the lesson date arrives before the tests pass, kill the live-scan plan for that lesson. The lesson itself — kids pick blocks, cat runs them, class fixes the bug — already works without this app.

## 13. Build order (suggested)

1. `blocks.py` + `app.py` + manual page: tap a sequence on the page, POST it to `/api/expand`, play the returned steps. No camera yet.
2. `generate_cards.py`: print one set, test size/distance at home.
3. `scanner.py` + `/api/scan`: one-photo scan → confirm screen → run. No live video.
4. Test plan §11, including the bug case and the AGAIN case.
5. Projector + classroom-light test.
6. Only then: decide whether it goes to St. Thomas More, or stays a home project for Benjamin.

## Open decisions for Anthony

- Say preset text: keep “Hi, we’re Utopia!” or change it?
- AGAIN default: keep ×3, or match the lesson’s ×4?
- Laptop webcam model / tripod you already own, or buy a cheap gooseneck mount?
- iPad v2 at all, or is laptop + projector enough for every use you actually have?
