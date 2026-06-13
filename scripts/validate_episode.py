#!/usr/bin/env python3
"""Validate an episode against the MANGA_FAILURE_REGISTRY checks.

Automates the red-team checklist so a flat, narration-only episode (the A1E01 failure)
cannot ship unnoticed. Works on the storyboard JSON or the built episode.json — both
carry panel.dialogue[]. Exit 1 if any HIGH-severity check fails.

Checks:
  M001 (HIGH)  >= 1 spoken `speech` line in the episode
  M002 (HIGH)  caption ratio <= ~1 per 3 panels
  M004 (MED)   >= 2 distinct named speakers (a two-hander is possible)
  M005 (MED)   no mystical-awe vocab in dialogue/captions
  M006 (MED)   no multiverse / twist-gate vocab (Arc I)
  M007 (MED)   no narrated pity/injustice for the Dimmed

Usage:
  python3 validate_episode.py <episode.json | storyboard.json> [--arc1]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MYSTIC = [
    r"\bgod(s|dess)?\b",
    r"\bdivine\b",
    r"glowing eyes",
    r"\bmagic",
    r"sun-?god",
    r"eyes of (fire|light|the sun)",
    r"\bsorcery\b",
    r"\bmiracle\b",
]
TWIST = [
    r"multiverse",
    r"parallel timeline",
    r"the commonality",
    r"world-?walk",
    r"divergent timeline",
    r"other world",
    r"alternate earth",
]
PITY = [
    r"\bunfair\b",
    r"\bdeserved\b",
    r"\bexploited\b",
    r"it wasn'?t (right|fair)",
    r"nobody thanked",
    r"\binjustice\b",
    r"\bpitied\b",
]


def load_panels(path: Path) -> list:
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("panels", [])
    return data


def all_text(panels):
    """Yield (panel_no, type, speaker, text) for every dialogue + legacy caption."""
    for p in panels:
        for d in p.get("dialogue", []) or []:
            yield (
                p.get("panel"),
                d.get("type", "speech"),
                d.get("speaker", ""),
                d.get("text", ""),
            )
        if p.get("caption"):
            yield p.get("panel"), "caption", p.get("caption_pov", ""), p["caption"]


def scan(rxs, text):
    return [rx for rx in rxs if re.search(rx, text, re.I)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument(
        "--arc1", action="store_true", help="enforce the Arc I twist-gate (M006)"
    )
    args = ap.parse_args()

    panels = load_panels(Path(args.path))
    n_panels = len(panels)
    entries = list(all_text(panels))
    speech = [e for e in entries if e[1] == "speech"]
    captions = [e for e in entries if e[1] == "caption"]
    speakers = sorted({e[2] for e in speech if e[2]})

    fails, warns, oks = [], [], []

    # M001 — at least one spoken line
    if speech:
        oks.append(f"M001 ok: {len(speech)} spoken line(s)")
    else:
        fails.append(
            "M001 FAIL: episode has NO spoken dialogue (narration-only — the A1E01 failure)"
        )

    # M002 — caption budget
    ratio = (len(captions) / n_panels) if n_panels else 0
    if ratio <= 0.34:
        oks.append(f"M002 ok: caption ratio {ratio:.2f} ({len(captions)}/{n_panels})")
    else:
        fails.append(
            f"M002 FAIL: caption ratio {ratio:.2f} > 0.34 ({len(captions)}/{n_panels} panels)"
        )

    # M004 — two-hander possible
    if len(speakers) >= 2:
        oks.append(f"M004 ok: {len(speakers)} named speakers ({', '.join(speakers)})")
    else:
        warns.append(
            f"M004 warn: only {len(speakers)} named speaker(s); a two-hander needs >=2"
        )

    # M005 / M006 / M007 — vocabulary red-teams
    for pno, _t, _spk, txt in entries:
        if scan(MYSTIC, txt):
            warns.append(
                f"M005 warn (panel {pno}): mystical-awe vocab — ground awe in real objects: {txt[:50]!r}"
            )
        if args.arc1 and scan(TWIST, txt):
            fails.append(
                f"M006 FAIL (panel {pno}): twist-gate breach (multiverse in Arc I): {txt[:50]!r}"
            )
        if scan(PITY, txt):
            warns.append(
                f"M007 warn (panel {pno}): narrated pity/injustice — show, don't editorialise: {txt[:50]!r}"
            )

    print(
        f"== validate {Path(args.path).name} : {n_panels} panels, {len(entries)} dialogue entries =="
    )
    for o in oks:
        print("  " + o)
    for w in warns:
        print("  " + w)
    for f in fails:
        print("  " + f)

    if fails:
        print(f"\nRESULT: {len(fails)} HIGH-severity failure(s). NOT shippable.")
        return 1
    print(f"\nRESULT: clean ({len(warns)} advisory warning(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
