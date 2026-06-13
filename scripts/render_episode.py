#!/usr/bin/env python3
"""Render panel variants for a manga_studio episode via Replicate FLUX.

Renders VARIANT-PASS-MAJOR: first variant 1 of every panel (a complete readthrough
fast), then variant 2 of every panel, then variant 3 — so the episode is reviewable
end-to-end as early as possible. Progress is saved into episode.json after every
image; re-running resumes where it stopped. Panels FLAGGED in the editor get their
existing variants kept and a fresh variant appended (regeneration workflow).

Blank lettering: if a panel has bubbles[], the prompt gains an instruction to draw
EMPTY speech/thought/caption boxes (no letters) at the requested anchors; the
negative prompt already bans text artifacts. Dialogue text itself is NEVER rendered;
it lives in panel.dialogue[] for the second lettering pass.

Usage:
  python3 render_episode.py <episode_dir> [--variants 3] [--max N] [--model schnell|dev|pro]
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import requests  # type: ignore

MODELS = {
    "schnell": "black-forest-labs/flux-schnell",
    "dev": "black-forest-labs/flux-dev",
    "pro": "black-forest-labs/flux-1.1-pro",
}
BUBBLE_TEXT = {
    "speech": "a clean white comic speech balloon with smooth outline and pointed tail, interior COMPLETELY BLANK white, no letters, no words",
    "thought": "a soft cloud-shaped comic thought bubble with small trailing circles, interior COMPLETELY BLANK white, no letters",
    "caption": "a rectangular comic caption box with thin border, interior COMPLETELY BLANK, no letters",
}

# FEEDBACK LOOP: map a reviewer's reject reason (note / fault chip) to a corrective
# phrase appended to the prompt on regeneration. The editor's fault chips are the keys;
# free-text notes are scanned for these substrings too. This closes the review->improve
# loop the system was missing — a flagged panel regenerates WITH the fix, not blindly.
FAULT_FIX = {
    "hands": "hands anatomically correct with exactly five fingers, no extra or fused fingers",
    "finger": "hands anatomically correct with exactly five fingers, no extra or fused fingers",
    "face drift": "consistent facial features matching the cast lock, stable face structure",
    "wrong character": "STRICTLY follow the CAST DIFFERENTIATION block; correct character identity and props",
    "text artifact": "absolutely no text, no letters, no glyphs, no signage anywhere in the image",
    "palette": "strictly adhere to the bronze-age living-world palette, no off-palette colours",
    "anatomy": "correct human anatomy, natural proportions, no distortion",
    "style drift": "maintain STYLE_SUNDERED_WEBTOON: dense ink linework, layered screentone, ligne-claire faces",
    "composition": "stronger clear composition with a single clear focal subject, rule-of-thirds framing",
}


def regen_suffix(note: str) -> str:
    """Build a corrective prompt suffix from a panel's reject note (feedback loop)."""
    if not note:
        return ""
    low = note.lower()
    fixes = []
    for key, fix in FAULT_FIX.items():
        if key in low and fix not in fixes:
            fixes.append(fix)
    if not fixes:
        return ""
    return " REGENERATION FIXES (address the prior fault): " + "; ".join(fixes) + "."


def load_token() -> str:
    import os

    if os.environ.get("REPLICATE_API_TOKEN"):
        return os.environ["REPLICATE_API_TOKEN"]
    env = Path.home() / ".config" / "qalarc-blog" / "replicate.env"
    for line in env.read_text().splitlines():
        m = re.match(
            r"\s*(?:export\s+)?REPLICATE_API_TOKEN\s*=\s*[\"']?([^\"'\s]+)", line
        )
        if m:
            return m.group(1)
    raise SystemExit("no REPLICATE_API_TOKEN")


def bubble_suffix(panel: dict) -> str:
    bits = []
    for b in panel.get("bubbles", []):
        kind = BUBBLE_TEXT.get(b.get("type", "speech"), BUBBLE_TEXT["speech"])
        anchor = b.get("anchor", "upper area")
        bits.append(f"{kind}, positioned {anchor}")
    return (" Comic lettering layout: " + "; ".join(bits) + ".") if bits else ""


def render_one(token: str, model: str, prompt: str, aspect: str) -> str | None:
    body = {
        "input": {
            "prompt": prompt[:1900],
            "aspect_ratio": aspect or "2:3",
            "output_format": "webp",
        }
    }
    if model.endswith("flux-schnell"):
        body["input"]["num_outputs"] = 1
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "wait",
    }
    r = None
    for attempt in range(8):
        r = requests.post(
            f"https://api.replicate.com/v1/models/{model}/predictions",
            headers=headers,
            json=body,
            timeout=180,
        )
        if r.status_code != 429:
            break
        time.sleep(int(r.headers.get("retry-after", 0)) or (12 + attempt * 6))
    if r is None or r.status_code not in (200, 201):
        return None
    d = r.json()
    for _ in range(60):
        if d.get("status") == "succeeded":
            out = d.get("output")
            return out[0] if isinstance(out, list) else out
        if d.get("status") in ("failed", "canceled"):
            return None
        gurl = d.get("urls", {}).get("get")
        if not gurl:
            return None
        time.sleep(2)
        d = requests.get(
            gurl, headers={"Authorization": f"Bearer {token}"}, timeout=60
        ).json()
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir")
    ap.add_argument("--variants", type=int, default=3)
    ap.add_argument("--max", type=int, default=0, help="stop after N renders this run")
    ap.add_argument("--model", choices=list(MODELS), default="schnell")
    ap.add_argument(
        "--regen",
        action="store_true",
        help="regenerate ONLY flagged panels, applying the reject-note fix to the prompt, "
        "clearing the flag and appending a fresh variant",
    )
    args = ap.parse_args()

    ep_dir = Path(args.episode_dir)
    ep_file = ep_dir / "episode.json"
    renders = ep_dir / "renders"
    renders.mkdir(exist_ok=True)
    token = load_token()
    model = MODELS[args.model]

    done = 0

    if args.regen:
        # FEEDBACK LOOP: regenerate only flagged panels, applying the reject-note fix.
        ep = json.load(open(ep_file, encoding="utf-8"))
        flagged = [p for p in ep["panels"] if p.get("flagged")]
        if not flagged:
            print("no flagged panels to regenerate.")
            return 0
        for panel in flagged:
            if args.max and done >= args.max:
                break
            n = panel["panel"]
            note = panel.get("note", "")
            k = len(panel["variants"]) + 1
            fn = f"panel_{n:02d}_v{k}r.webp"
            fix = regen_suffix(note)
            prompt = panel["prompt"] + bubble_suffix(panel) + fix
            print(f"REGEN panel {n:>2} (note: {note[:40]!r}) … ", end="", flush=True)
            uri = render_one(token, model, prompt, panel.get("aspect", "2:3"))
            if not uri:
                print("FAILED")
                continue
            try:
                urllib.request.urlretrieve(uri, renders / fn)
            except Exception as e:  # noqa: BLE001
                print("download failed:", e)
                continue
            panel["variants"].append(
                {
                    "file": f"renders/{fn}",
                    "model": model,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "regen_from_note": note,
                    "applied_fix": fix.strip(),
                }
            )
            # point reviewer at the new variant; clear flag so it re-enters review
            panel["selected_variant"] = len(panel["variants"]) - 1
            panel["flagged"] = False
            done += 1
            print("ok" + (" (+fix)" if fix else " (no mapped fix)"))
            json.dump(
                ep, open(ep_file, "w", encoding="utf-8"), indent=2, ensure_ascii=False
            )
            time.sleep(11)
        print(f"\nregenerated {done} flagged panel(s)")
        return 0

    for vpass in range(1, args.variants + 1):  # variant-pass-major
        ep = json.load(open(ep_file, encoding="utf-8"))
        for panel in ep["panels"]:
            if args.max and done >= args.max:
                json.dump(
                    ep,
                    open(ep_file, "w", encoding="utf-8"),
                    indent=2,
                    ensure_ascii=False,
                )
                print(f"\nstopped at --max {args.max}")
                return 0
            n = panel["panel"]
            fn = f"panel_{n:02d}_v{vpass}.webp"
            if (
                any(v.get("file") == f"renders/{fn}" for v in panel["variants"])
                and (renders / fn).exists()
            ):
                continue
            prompt = panel["prompt"] + bubble_suffix(panel)
            print(
                f"panel {n:>2} v{vpass} [{panel.get('scroll_beat', '')[:24]:24}] … ",
                end="",
                flush=True,
            )
            uri = render_one(token, model, prompt, panel.get("aspect", "2:3"))
            if not uri:
                print("FAILED")
                continue
            try:
                urllib.request.urlretrieve(uri, renders / fn)
            except Exception as e:  # noqa: BLE001
                print("download failed:", e)
                continue
            panel["variants"].append(
                {
                    "file": f"renders/{fn}",
                    "model": model,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            done += 1
            print("ok")
            json.dump(
                ep, open(ep_file, "w", encoding="utf-8"), indent=2, ensure_ascii=False
            )
            time.sleep(11)  # replicate throttle (~6/min)
    print(f"\nrendered {done} image(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
