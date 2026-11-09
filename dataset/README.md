# Benchmark dataset

Reference animation plus manipulated test cases with known ground truth (CF-01, DS-01 to DS-06).

## Use case

In-vehicle infotainment menu (800 × 480 px, 30 fps, 4 s):

| Time | Event |
|---|---|
| 0.0 s | Menu shown, focus on "Navigation" |
| 0.6 s | Focus slides to "Medien" (250 ms, ease-in-out) |
| 1.2 s | Focus slides to "Telefon" (250 ms) |
| 1.8 s | "Telefon" is selected (press feedback, 200 ms) |
| 2.0 s | Pop-up "Telefon verbunden" fades/scales in (300 ms) |

Preview in a browser: open `animation/menu.html`. Parameters can be passed as JSON, for example
`animation/menu.html?p={"popupDelay":800}`.

## Files

| Path | Content |
|---|---|
| `animation/menu.html` | Parametric animation; each frame is a pure function of time `t` |
| `testcases.json` | **Specification**: which manipulation produces which test case and its label |
| `generate.py` | Generator: renders, manipulates and encodes all videos |
| `videos/` | Generated MP4 files (H.264) |
| `testcases.csv` | Generated manifest: ID, label, error type, category, parameters, SHA-256 |

## Test cases

| ID | Expected | Error type | Category | What is different |
|---|---|---|---|---|
| REF-001 | OK | – | – | Reference animation |
| TC-001 | OK | none | – | Identical copy (true negative) |
| TC-002 | OK | none | – | Stronger compression (CRF 32) |
| TC-003 | OK *(edge)* | popup_delay | timing | Pop-up 40 ms late, within tolerance |
| TC-004 | OK *(edge)* | highlight_timing | timing | Highlight 280 ms instead of 250 ms |
| TC-005 | OK *(edge)* | none | – | Slight capture noise |
| TC-010 | NOK | popup_delay | timing | Pop-up 500 ms late |
| TC-011 | NOK | popup_delay | timing | Pop-up 1200 ms late |
| TC-012 | NOK | highlight_timing | timing | Highlight jumps (0 ms) instead of sliding |
| TC-013 | NOK | highlight_timing | timing | Second focus step 500 ms late |
| TC-014 | NOK | animation_speed | timing | Pop-up appears without fade-in |
| TC-015 | NOK | frame_freeze | timing | Display freezes for 500 ms |
| TC-020 | NOK | missing_element | display | Menu item "Klima" missing |
| TC-021 | NOK | missing_element | display | Pop-up icon missing |
| TC-022 | NOK | wrong_content | display | Wrong pop-up text |
| TC-023 | NOK | wrong_content | display | Highlight red instead of blue |
| TC-024 | NOK | flicker | display | Screen darkens twice for 2 frames |

Total: 5 OK (3 of them edge cases) and 11 NOK.

## How the manipulations are made (DS-06)

There are three levels, chosen by where such an error would occur in reality:

1. **Animation logic** (`params`): changes the parameters of the animation itself, such as
   delays, durations, hidden elements, text or colour. These are errors in the implementation
   of the animation.
2. **Frame level** (`freeze`): the same frame is repeated for a period of time, which simulates
   a display or rendering stall.
3. **Video level** (`post`, FFmpeg): flicker (darkened frames), noise or compression. These
   simulate display or capture effects.

Rendering is frame-exact: the browser does not play the animation in real time. The generator
calls `renderAt(t)` for every frame time and takes a screenshot. Encoding uses fixed FFmpeg
settings (`bitexact`, single thread). Running the generator again on the same machine produces
**byte-identical** files (compare the `sha256` column). Other machines may differ slightly
because font rendering differs.

**Tolerance assumption** (still to be confirmed with ALTEN): deviations up to about 1–2 frames
(≈ 50 ms) count as OK. This is why TC-003 and TC-004 are labelled OK.

## Regenerate

```bash
cd dataset
pip install -r requirements.txt
playwright install chromium
python generate.py                 # everything
python generate.py TC-010 TC-024   # selected cases only
```

FFmpeg does not have to be installed: if `ffmpeg` is not on the PATH, the binary from
`imageio-ffmpeg` is used.

To add a test case, add an entry to `testcases.json` and run the generator.
