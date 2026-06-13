#!/usr/bin/env python3
"""Second-pass LETTERING — composite panel.dialogue[] onto the approved render.

This is the missing step the pipeline was designed around: FLUX generates text-free
images (it letters badly), the SCRIPT step writes dialogue into panel.dialogue[], and
THIS script bakes that dialogue onto the chosen variant — drawing the bubble shapes and
the words, positioned by each entry's `anchor`.

It NEVER asks the model to render text. It draws bubbles with PIL over the existing
image, so the lettering is crisp and editable (re-run after editing dialogue/anchors).

Per dialogue entry (type / speaker / text / anchor):
  speech  -> rounded white balloon + tail toward speaker side, black text
  thought -> soft cloud bubble + trailing dots, italic text
  caption -> rectangular box, top or bottom band, serif text (the narration seasoning)
  sfx     -> no bubble; bold outlined onomatopoeia placed at the anchor

Output: episodes/<id>/lettered/panel_NN.webp  (originals never touched)

Usage:
  python3 letter_episode.py <episode_dir> [--all] [--panels 1,2,7] [--font PATH]
    default: letter only APPROVED panels. --all letters every panel with a variant.
"""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Font discovery — prefer condensed sans for speech, serif for captions. Fall back
# gracefully so the script runs on any box with DejaVu (PIL ships nothing reliable).
FONT_CANDIDATES = {
    "sans": [
        "/usr/share/fonts/TTF/DejaVuSansCondensed.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf",
    ],
    "sans_bold": [
        "/usr/share/fonts/TTF/DejaVuSansCondensed-Bold.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ],
    "serif_italic": [
        "/usr/share/fonts/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/TTF/DejaVuSerif-Italic.ttf",
    ],
    "serif": [
        "/usr/share/fonts/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSerifCondensed.ttf",
        "/usr/share/fonts/TTF/DejaVuSerif.ttf",
    ],
}

ANCHORS = {
    "top-left": (0.04, 0.04, "lt"),
    "top-center": (0.50, 0.04, "ct"),
    "top-right": (0.96, 0.04, "rt"),
    "center": (0.50, 0.50, "cc"),
    "bottom-left": (0.04, 0.96, "lb"),
    "bottom-center": (0.50, 0.96, "cb"),
    "bottom-right": (0.96, 0.96, "rb"),
    "auto": (0.04, 0.04, "lt"),
    "upper area": (0.50, 0.06, "ct"),
}


def _load(paths, size):
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def fonts_for(width, override=None):
    base = max(15, int(width * 0.034))  # scale type to panel width
    sans_paths = (
        [override] + FONT_CANDIDATES["sans"] if override else FONT_CANDIDATES["sans"]
    )
    return {
        "speech": _load(sans_paths, base),
        "thought": _load(FONT_CANDIDATES["serif_italic"], base),
        "caption": _load(FONT_CANDIDATES["serif"], int(base * 0.92)),
        "sfx": _load(FONT_CANDIDATES["sans_bold"], int(base * 1.9)),
        "name": _load(FONT_CANDIDATES["sans_bold"], int(base * 0.7)),
    }


def wrap_to(draw, text, font, max_w):
    """Greedy wrap so the longest line fits max_w pixels."""
    if not text:
        return [""]
    # estimate chars-per-line from average glyph width, then refine
    avg = max(6, draw.textlength("abcdefghij", font=font) / 10)
    width_chars = max(8, int(max_w / avg))
    lines = []
    for para in text.split("\n"):
        wrapped = textwrap.wrap(para, width=width_chars) or [""]
        # shrink any line still too wide
        for ln in wrapped:
            while draw.textlength(ln, font=font) > max_w and " " in ln:
                ln = ln.rsplit(" ", 1)[0]
            lines.append(ln)
    return lines


def text_box(draw, lines, font, pad):
    w = max((draw.textlength(ln, font=font) for ln in lines), default=0)
    asc, desc = font.getmetrics()
    lh = asc + desc + 3
    return int(w + pad * 2), int(lh * len(lines) + pad * 2), lh


def place_xy(anchor, W, H, bw, bh):
    fx, fy, _ = ANCHORS.get(anchor, ANCHORS["auto"])
    x = fx * W - (bw if fx > 0.6 else (bw / 2 if 0.4 < fx < 0.6 else 0))
    y = fy * H - (bh if fy > 0.6 else (bh / 2 if 0.4 < fy < 0.6 else 0))
    x = max(8, min(W - bw - 8, x))
    y = max(8, min(H - bh - 8, y))
    return int(x), int(y)


def draw_text_block(draw, x, y, lines, font, lh, pad, fill=(20, 20, 24)):
    cy = y + pad
    for ln in lines:
        draw.text((x + pad, cy), ln, font=font, fill=fill)
        cy += lh


def letter_speech(draw, img, entry, fonts, W, H, kind):
    font = fonts["thought" if kind == "thought" else "speech"]
    text = entry.get("text", "")
    speaker = entry.get("speaker", "")
    max_w = int(W * 0.62)
    lines = wrap_to(draw, text, font, max_w)
    bw, bh, lh = text_box(draw, lines, font, pad=int(W * 0.03))
    name_h = int(fonts["name"].size + 4) if speaker else 0
    bh += name_h
    x, y = place_xy(entry.get("anchor", "auto"), W, H, bw, bh)
    pad = int(W * 0.03)
    if kind == "thought":
        draw.rounded_rectangle(
            [x, y, x + bw, y + bh],
            radius=int(bh * 0.32),
            fill=(252, 252, 250),
            outline=(30, 30, 36),
            width=3,
        )
        # trailing thought dots toward nearest corner
        for i, r in enumerate((7, 5, 3)):
            draw.ellipse(
                [
                    x + 6 + i * 14,
                    y + bh + 4 + i * 12,
                    x + 6 + i * 14 + r * 2,
                    y + bh + 4 + i * 12 + r * 2,
                ],
                fill=(252, 252, 250),
                outline=(30, 30, 36),
                width=2,
            )
    else:
        draw.rounded_rectangle(
            [x, y, x + bw, y + bh],
            radius=int(bh * 0.18),
            fill=(253, 253, 251),
            outline=(20, 20, 26),
            width=3,
        )
        # speech tail (small triangle toward bottom)
        tx = x + int(bw * 0.5)
        draw.polygon(
            [(tx - 10, y + bh - 2), (tx + 10, y + bh - 2), (tx, y + bh + 16)],
            fill=(253, 253, 251),
            outline=(20, 20, 26),
        )
    ty = y
    if speaker:
        draw.text(
            (x + pad, y + 4), speaker.upper(), font=fonts["name"], fill=(150, 90, 40)
        )
        ty = y + name_h
    draw_text_block(draw, x, ty, lines, font, lh, pad)


def letter_caption(draw, img, entry, fonts, W, H):
    font = fonts["caption"]
    text = entry.get("text", "")
    speaker = entry.get("speaker", "")
    max_w = int(W * 0.9)
    lines = wrap_to(draw, text, font, max_w)
    pad = int(W * 0.025)
    bw, bh, lh = text_box(draw, lines, font, pad)
    bw = int(W * 0.92)
    anchor = entry.get("anchor", "top-left")
    top = "top" in anchor
    x = int(W * 0.04)
    y = 10 if top else H - bh - 10
    draw.rectangle(
        [x, y, x + bw, y + bh], fill=(24, 22, 18), outline=(196, 164, 107), width=2
    )
    if speaker:
        draw.text(
            (x + pad, y + 4), speaker.upper(), font=fonts["name"], fill=(196, 164, 107)
        )
        draw_text_block(
            draw,
            x,
            y + int(fonts["name"].size),
            lines,
            font,
            lh,
            pad,
            fill=(232, 230, 224),
        )
    else:
        draw_text_block(draw, x, y, lines, font, lh, pad, fill=(232, 230, 224))


def letter_sfx(draw, entry, fonts, W, H):
    font = fonts["sfx"]
    text = entry.get("text", "")
    bw = draw.textlength(text, font=font)
    bh = font.size
    x, y = place_xy(entry.get("anchor", "center"), W, H, int(bw), int(bh))
    # outline for punch
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            draw.text((x + dx, y + dy), text, font=font, fill=(20, 20, 24))
    draw.text((x, y), text, font=font, fill=(232, 196, 120))


def letter_panel(src_path, dialogue, font_override=None):
    img = Image.open(src_path).convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    fonts = fonts_for(W, font_override)
    # captions first (bands), then bubbles, then sfx on top
    order = {"caption": 0, "speech": 1, "thought": 1, "sfx": 2}
    for entry in sorted(dialogue, key=lambda e: order.get(e.get("type", "speech"), 1)):
        t = entry.get("type", "speech")
        if not entry.get("text"):
            continue
        if t == "caption":
            letter_caption(draw, img, entry, fonts, W, H)
        elif t == "sfx":
            letter_sfx(draw, entry, fonts, W, H)
        else:
            letter_speech(draw, img, entry, fonts, W, H, t)
    return Image.alpha_composite(img, overlay).convert("RGB")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir")
    ap.add_argument(
        "--all",
        action="store_true",
        help="letter every panel with a variant (not just approved)",
    )
    ap.add_argument(
        "--panels", default="", help="comma list of panel numbers to letter"
    )
    ap.add_argument("--font", default=None, help="override speech font TTF path")
    args = ap.parse_args()

    ep_dir = Path(args.episode_dir)
    ep = json.load(open(ep_dir / "episode.json", encoding="utf-8"))
    out_dir = ep_dir / "lettered"
    out_dir.mkdir(exist_ok=True)
    only = (
        {int(x) for x in args.panels.split(",") if x.strip().isdigit()}
        if args.panels
        else None
    )

    done = 0
    for p in ep["panels"]:
        if only and p["panel"] not in only:
            continue
        if not args.all and not only and not p.get("approved"):
            continue
        if not p.get("variants"):
            continue
        dlg = list(p.get("dialogue", []))
        # also honour a legacy single caption field
        if p.get("caption"):
            dlg = dlg + [
                {
                    "type": "caption",
                    "speaker": p.get("caption_pov", ""),
                    "text": p["caption"],
                    "anchor": "top-left",
                }
            ]
        if not dlg:
            continue
        vfile = p["variants"][
            min(p.get("selected_variant", 0), len(p["variants"]) - 1)
        ]["file"]
        src = ep_dir / vfile
        if not src.exists():
            print(f"panel {p['panel']:>2}: variant missing ({vfile}) — skip")
            continue
        out = out_dir / f"panel_{p['panel']:02d}.webp"
        letter_panel(src, dlg, args.font).save(out, "WEBP", quality=92)
        print(f"panel {p['panel']:>2}: lettered {len(dlg)} entries -> {out.name}")
        done += 1
    print(f"\nlettered {done} panel(s) -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
