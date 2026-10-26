"""Block definitions, program semantics, and validation for scratch-jr-irl.

Step 1 only: manual programs built by tapping blocks on the webpage.
No camera, no scanner here. Scanner (Step 3) will map ArUco marker IDs
to these same block types via MARKER_IDS.

Semantics (from the MVP spec, deliberately simple):
- GO is a trigger, not an action.
- Walk / Jump / Spin / Say are actions, in left-to-right order.
- AGAIN must be last. It repeats ALL action blocks before it.
  AGAIN with count=3 means the actions run 3 times total, not 3 extra times.
  No count given defaults to 3.
- Say uses a preset text in v1. No typing, no OCR.
- Max 10 action blocks before AGAIN.
- If Walk would push the cat off the right edge, the cat stops at the edge.
  That is handled by the player (clamping), not by expansion.
"""

SAY_TEXT = "Hi, we're Utopia!"

BLOCKS = {
    "GO": {"type": "GO", "label": "GO", "kid_name": "GO button", "color": "#FFD500"},
    "WALK": {"type": "WALK", "label": "Walk", "kid_name": "Walk", "color": "#0096FF"},
    "JUMP": {"type": "JUMP", "label": "Jump", "kid_name": "Jump", "color": "#0096FF"},
    "SPIN": {"type": "SPIN", "label": "Spin", "kid_name": "Spin", "color": "#0096FF"},
    "SAY": {"type": "SAY", "label": "Talk", "kid_name": "Talk", "color": "#9B59D0"},
    "AGAIN": {"type": "AGAIN", "label": "AGAIN", "kid_name": "AGAIN block", "color": "#FF7F00"},
}

# ArUco DICT_4X4_50 marker IDs, reserved for Step 3 (scanner).
MARKER_IDS = {
    0: "GO",
    1: "WALK",
    2: "JUMP",
    3: "SPIN",
    4: "SAY",
    5: "AGAIN",
    10: "COUNT_2",
    11: "COUNT_3",
    12: "COUNT_4",
}

DURATIONS_MS = {
    "WALK": 600,
    "JUMP": 600,
    "SPIN": 800,
    "SAY": 2500,
}

MAX_ACTIONS = 10


def normalize_block(raw):
    """Return a clean block dict, or None for an unknown block."""
    if not isinstance(raw, dict):
        return None
    block_type = raw.get("type")
    if block_type not in BLOCKS:
        return None
    block = dict(BLOCKS[block_type])
    if block_type == "AGAIN":
        count = raw.get("count", 3)
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 3
        block["count"] = count if count in (2, 3, 4) else 3
    if block_type == "SAY":
        block["say_text"] = raw.get("say_text") or SAY_TEXT
    return block


def expand_program(raw_program, say_text=None):
    """Validate a tapped program and expand AGAIN into execution steps.

    Returns a dict with:
      program: normalized blocks as tapped
      steps: expanded action steps to play, in order ([] on a hard error)
      warnings: plain-language warnings for the confirm screen
      hard_error: True when the program should not run as-is
    """
    program = []
    warnings = []
    for raw in raw_program or []:
        block = normalize_block(raw)
        if block is None:
            warnings.append("Unknown block in the program — remove it and try again.")
        else:
            if block["type"] == "SAY" and say_text:
                block["say_text"] = say_text
            program.append(block)

    if not program:
        return {"program": [], "steps": [], "warnings": ["No blocks yet. Tap some blocks first."], "hard_error": True}

    types = [b["type"] for b in program]

    if "GO" not in types:
        warnings.append("No GO block. The cat will still run, but GO should go first.")
    if types.count("GO") > 1:
        warnings.append("More than one GO block. Only the first one is needed.")
    if types.count("SAY") > 1:
        warnings.append("More than one Talk block. Only one is needed in v1.")
    if types.count("AGAIN") > 1:
        warnings.append("More than one AGAIN block. Only one is needed, and it goes last.")

    again_index = types.index("AGAIN") if "AGAIN" in types else None
    hard_error = False
    if again_index is not None and again_index != len(program) - 1:
        warnings.append("AGAIN has to go last. Move it to the end.")
        hard_error = True

    actions = [b for b in program if b["type"] not in ("GO", "AGAIN")]
    if len(actions) > MAX_ACTIONS:
        warnings.append(f"Too many action blocks (max {MAX_ACTIONS}). Shorten the program.")
        hard_error = True

    if hard_error:
        return {"program": program, "steps": [], "warnings": warnings, "hard_error": True}

    repeat = 1
    if again_index is not None:
        repeat = program[again_index].get("count", 3)

    steps = []
    for _ in range(repeat):
        for action in actions:
            step = dict(action)
            step["duration_ms"] = DURATIONS_MS[action["type"]]
            steps.append(step)

    return {"program": program, "steps": steps, "warnings": warnings, "hard_error": False}
