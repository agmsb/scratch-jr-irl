"""Generate printable physical cards for scratch-jr-irl.

Each card is a PNG in cards/:
  - ScratchJr colour header + big word (GO, WALK, JUMP, SPIN, TALK, AGAIN, 2x, 3x, 4x)
  - ArUco marker (DICT_4X4_50) in the bottom-right corner, at least
    2.0 inches square when printed at 100% — see README for print notes.

Run:
    pip install opencv-python
    python cards/generate_cards.py
    # then print cards/*.png at 100% on matte cardstock, not glossy

Card size in the PNG is 1000 x 800 px, designed for ~5 x 4 inches at
200 dpi. If your printer scales it, re-check the marker size with a ruler:
the black-and-white square (including its white border) should be
at least 2.0 inches on a side.

These PNGs are generated locally and are NOT committed to git by the
snapshot push (binary files are excluded). Run this script on any
machine that needs a fresh set.
"""

import os
import sys

try:
    import cv2
    import numpy as np
except ImportError:
    print("Install OpenCV first: pip install opencv-python")
    sys.exit(1)

# Marker IDs and words are duplicated here on purpose, so this script
# can run standalone from cards/ without importing blocks.py.
# They must match blocks.MARKER_IDS in the spec.

# marker_id -> (word, colour) for cards. Colours match blocks.py.
CARDS = [
    (0, "GO", "#FFD500"),
    (1, "WALK", "#0096FF"),
    (2, "JUMP", "#0096FF"),
    (3, "SPIN", "#0096FF"),
    (4, "TALK", "#9B59D0"),
    (5, "AGAIN", "#FF7F00"),
    (10, "2 TIMES", "#FF7F00"),
    (11, "3 TIMES", "#FF7F00"),
    (12, "4 TIMES", "#FF7F00"),
]

# How many copies of each card to print by default.
COPIES = {0: 1, 1: 3, 2: 2, 3: 2, 4: 1, 5: 1, 10: 1, 11: 1, 12: 1}


def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return (b, g, r)


def make_card(marker_id, word, colour, out_path):
    width, height = 1000, 800
    card = np.full((height, width, 3), 255, dtype=np.uint8)
    # Colour header
    cv2.rectangle(card, (0, 0), (width, 300), hex_to_bgr(colour), -1)
    # Word, centred in the header
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, _th), _ = cv2.getTextSize(word, font, 2.2, 4)
    cv2.putText(card, word, ((width - tw) // 2, 190), font, 2.2, (0, 0, 0), 4, cv2.LINE_AA)
    # Marker, bottom-right, 400 px square + white border is already in the
    # generated marker image; keep a clean white margin around it.
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, 400)
    marker_bgr = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
    card[350:750, 550:950] = marker_bgr
    # Marker ID in small print, for the teacher (not for the camera)
    cv2.putText(card, f"marker {marker_id}", (40, 760), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (80, 80, 80), 2, cv2.LINE_AA)
    cv2.imwrite(out_path, card)
    return out_path


def main():
    out_dir = os.path.join(os.path.dirname(__file__))
    os.makedirs(out_dir, exist_ok=True)
    # blocks.py lives one level up; make sure it imports when run as a script
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    for marker_id, word, colour in CARDS:
        for copy in range(1, COPIES.get(marker_id, 1) + 1):
            name = f"{word.lower().replace(' ', '_')}_{marker_id}_{copy}.png"
            path = make_card(marker_id, word, colour, os.path.join(out_dir, name))
            print(path)


if __name__ == "__main__":
    main()
