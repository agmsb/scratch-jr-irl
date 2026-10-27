"""Step 3 scanner: one photo -> program blocks.

Scan-on-demand only. Never live video tracking in v1.

Input: image bytes (a photo of physical cards in one row, left to right).
Output: a dict with:
  program: blocks in detected order, ready for blocks.expand_program()
           (AGAIN + following count tile are combined into one AGAIN block)
  detections: raw marker detections, sorted by centre x
  warnings: plain-language warnings for the confirm screen

Marker dictionary: DICT_4X4_50, IDs from blocks.MARKER_IDS.
  0 GO, 1 WALK, 2 JUMP, 3 SPIN, 4 SAY, 5 AGAIN,
  10 COUNT_2, 11 COUNT_3, 12 COUNT_4

Rules from the spec:
- Sort by centre x. That is the program order.
- Row check: if centres vary in y by more than ~1.5x a marker height,
  warn "cards are not in one row" but still return the sorted program.
- Rotation check: if a marker is rotated >45 degrees from upright,
  warn, but still accept its ID.
- Unknown marker IDs are never silently dropped: they become a warning
  and an "unknown card" placeholder position in detections.
- A count tile only means something right after AGAIN. Otherwise warn.
- Duplicates of GO / SAY / AGAIN are warnings, not silent drops;
  expand_program() will also flag them on the confirm screen.
"""

import math

try:
    import cv2
    import numpy as np
except ImportError:  # pragma: no cover - opencv is a Step 3 dependency
    cv2 = None
    np = None

from blocks import MARKER_IDS, normalize_block


def _rotation_degrees(corners):
    """Estimate upright rotation from a marker's 4 corners.

    OpenCV returns corners in order: top-left, top-right, bottom-right,
    bottom-left (for an upright marker). The angle of the top edge
    relative to horizontal is a good enough upright check for v1.
    """
    (x0, y0), (x1, y1) = corners[0], corners[1]
    return math.degrees(math.atan2(y1 - y0, x1 - x0))


def scan_image_bytes(image_bytes):
    """Scan one photo (bytes) and return program + warnings."""
    if cv2 is None:
        return {
            "program": [],
            "detections": [],
            "warnings": ["OpenCV is not installed. Run: pip install opencv-python"],
            "hard_error": True,
        }
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        return {"program": [], "detections": [], "warnings": ["Could not read that photo. Try another photo."], "hard_error": True}
    return scan_image(image)


def scan_image(image):
    """Scan an OpenCV image (BGR numpy array)."""
    if cv2 is None:
        return {"program": [], "detections": [], "warnings": ["OpenCV is not installed."], "hard_error": True}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, params)
    corners_list, ids, _rejected = detector.detectMarkers(gray)

    warnings = []
    detections = []
    if ids is None or len(ids) == 0:
        return {
            "program": [],
            "detections": [],
            "warnings": [
                "No cards found. Move the camera closer, turn the light on, "
                "and make sure the black-and-white squares are showing."
            ],
            "hard_error": True,
        }

    for corners, marker_id in zip(corners_list, ids.flatten()):
        pts = [(float(x), float(y)) for x, y in corners[0]]
        cx = sum(p[0] for p in pts) / 4.0
        cy = sum(p[1] for p in pts) / 4.0
        height = max(p[1] for p in pts) - min(p[1] for p in pts)
        rotation = _rotation_degrees(pts)
        detections.append({
            "marker_id": int(marker_id),
            "block_type": MARKER_IDS.get(int(marker_id)),
            "centre_x": cx,
            "centre_y": cy,
            "height": height,
            "rotation_degrees": round(rotation, 1),
        })

    detections.sort(key=lambda d: d["centre_x"])

    # Row check
    heights = [d["height"] for d in detections if d["height"] > 0]
    if heights and detections:
        y_spread = max(d["centre_y"] for d in detections) - min(d["centre_y"] for d in detections)
        if y_spread > 1.5 * (sum(heights) / len(heights)):
            warnings.append("Cards are not in one row. Put them on the guide line, left to right, and scan again.")

    for d in detections:
        if abs(d["rotation_degrees"]) > 45:
            warnings.append(f"Card in position {detections.index(d) + 1} looks rotated. Keep cards upright if you can.")

    # Build program, combining AGAIN + count tile, flagging unknowns.
    program = []
    i = 0
    while i < len(detections):
        d = detections[i]
        block_type = d["block_type"]
        if block_type is None:
            warnings.append(f"Unknown card in position {i + 1} (marker {d['marker_id']}). It was not added to the program.")
            i += 1
            continue
        if block_type.startswith("COUNT_"):
            # A count tile only counts right after AGAIN, and the AGAIN
            # block was already added just before it.
            if program and program[-1]["type"] == "AGAIN":
                program[-1]["count"] = int(block_type.split("_")[1])
            else:
                warnings.append(f"Number card in position {i + 1} without an AGAIN block before it. It was ignored.")
            i += 1
            continue
        block = normalize_block({"type": block_type})
        if block is not None:
            program.append(block)
        i += 1

    return {"program": program, "detections": detections, "warnings": warnings, "hard_error": False}
