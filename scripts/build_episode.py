#!/usr/bin/env python3
"""Build a manga_studio episode.json from a storyboard prompts JSON.

Transforms the flat storyboard prompt list into the studio's master episode schema:
  * variants[] (3 slots per panel) + selected_variant + approved/flagged/note  (editing)
  * dialogue[] (read from the SCRIPT step in the storyboard if present, else empty;
    shown UNDER the image during review) + bubbles[] (blank speech/thought/caption
    boxes rendered INTO the image with NO text)
  * animation{} defaults per shot type (motion hints usable by video-AI pipelines)
  * cast visual-ID block appended to multi-character prompts so the leads stay
    visually distinct (user feedback #1)

Usage:
  python3 build_episode.py <storyboard.json> <episode_dir> "<episode title>"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Cast appearance is the SINGLE SOURCE OF TRUTH in continuity/characters.json so a
# face/silhouette is fixed in ONE place and cannot drift between episodes. We build the
# CAST DIFFERENTIATION block from it; if the file is absent we fall back to the literal
# block below (keeps the script self-contained / backward-compatible).
CONTINUITY = Path(__file__).resolve().parents[1] / "continuity" / "characters.json"

_FALLBACK_CAST = (
    "CAST DIFFERENTIATION (each face/silhouette clearly distinct): "
    "Signe = tight pale braid, angular precise bearing, geometric-border garment wrap; "
    "Aldric = the tallest figure, short ash-blonde hair, rigid stillness, blade at hip; "
    "Cael = loose tousled ash-fair hair, relaxed slouch, freckles, small satchel case; "
    "Marit = warm honey-toned hair in a low tie with local cloth, soft open posture, worn notebook; "
    "Oswin = compact build, cropped dark hair, unreadable neutral face, plain dress; "
    "Dimmed workers (Brenn/Ysel/Toran) = warm amber-olive skin, practical work clothes, "
    "Brenn broad and weathered, Ysel braided and bright-eyed, Toran lean and quiet."
)


def load_cast() -> tuple[str, tuple]:
    """Build the cast-differentiation block + lead-name list from the continuity file."""
    try:
        data = json.load(open(CONTINUITY, encoding="utf-8"))
        chars = data.get("characters", {})
        if not chars:
            raise ValueError("empty")
        parts = [f"{name} = {c['appearance_lock']}" for name, c in chars.items()]
        block = (
            "CAST DIFFERENTIATION (each face/silhouette clearly distinct): "
            + "; ".join(parts)
            + "."
        )
        return block, tuple(chars.keys())
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return _FALLBACK_CAST, (
            "Signe",
            "Aldric",
            "Cael",
            "Marit",
            "Oswin",
            "Brenn",
            "Ysel",
            "Toran",
        )


CAST_VISUAL_ID, LEADS = load_cast()

ANIM_BY_SHOT = {
    "cover_splash": {
        "camera": "slow_zoom_in",
        "motion_hint": "dust drift, heat shimmer",
        "duration_s": 3.5,
        "transition": "fade",
    },
    "establishing": {
        "camera": "slow_pan_right",
        "motion_hint": "wind in scrub, distant sea glitter",
        "duration_s": 3.0,
        "transition": "cut",
    },
    "wide": {
        "camera": "slow_zoom_in",
        "motion_hint": "ambient drift",
        "duration_s": 2.5,
        "transition": "cut",
    },
    "insert": {
        "camera": "hold",
        "motion_hint": "subtle focus pull",
        "duration_s": 1.5,
        "transition": "cut",
    },
    "close": {
        "camera": "slow_zoom_in",
        "motion_hint": "breathing, eye micro-movement",
        "duration_s": 2.0,
        "transition": "cut",
    },
    "action": {
        "camera": "tracking",
        "motion_hint": "primary action loops once",
        "duration_s": 2.0,
        "transition": "cut",
    },
}


def anim_for(shot: str) -> dict:
    s = (shot or "").lower()
    for key, cfg in ANIM_BY_SHOT.items():
        if key in s:
            return dict(cfg)
    if "splash" in s:
        return dict(ANIM_BY_SHOT["cover_splash"])
    return dict(ANIM_BY_SHOT["wide"])


def main() -> int:
    src, out_dir, title = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    data = json.load(open(src, encoding="utf-8"))
    # Accept either a bare list of panels OR a script wrapper {"panels": [...], ...}
    # (the SCRIPT step's output may carry top-level metadata like "_demo"/"_script").
    panels = data["panels"] if isinstance(data, dict) else data
    out: dict = {
        "schema": "manga_studio/episode@1",
        "episode_id": out_dir.name,
        "title": title,
        "source_storyboard": str(src),
        "style_lock": {
            "style_token": "STYLE_SUNDERED_WEBTOON",
            "palette": "bronze-age living world: sky #C8A96E, earth #8B6E45, shadow #3D2810, sea #2D6A8A, regnant skin #F4F1EC",
            "cast_visual_id": CAST_VISUAL_ID,
            "inspiration": "isekai + survival manga pacing (Dr. Stone, Vinland Saga, Sousei no Taiga): competence beats, nature as antagonist, knowledge inserts",
            "lettering": "ALL text boxes / speech bubbles / thought bubbles rendered BLANK in-image; dialogue lives in panel.dialogue[] and is lettered in a second pass",
        },
        "render_defaults": {
            "model": "black-forest-labs/flux-schnell",
            "variants_per_panel": 3,
        },
        "panels": [],
    }
    for p in panels:
        prompt = p.get("prompt", "")
        if sum(1 for n in LEADS if n in prompt) >= 2:
            prompt = prompt + " " + CAST_VISUAL_ID
        out["panels"].append(
            {
                "panel": p.get("panel"),
                "scroll_beat": p.get("scroll_beat", ""),
                "shot": p.get("shot", ""),
                "aspect": p.get("aspect", "2:3"),
                "prompt": prompt,
                "negative_prompt": p.get("negative_prompt", ""),
                "caption": p.get("caption", ""),
                "caption_pov": p.get("caption_pov", ""),
                # SECOND-PASS LETTERING: content stays blank in the image; entries here
                # appear UNDER the image in the editor during review.
                # Read from the storyboard if the SCRIPT step authored them; else default
                # to [] (backward-compatible with un-scripted storyboards).
                "dialogue": p.get(
                    "dialogue", []
                ),  # [{type: speech|thought|caption|sfx, speaker, text, anchor}]
                "bubbles": p.get(
                    "bubbles", []
                ),  # [{type: speech|thought|caption, anchor: top-left|...}] -> rendered BLANK
                "variants": [],  # [{file, model, created_at}]
                "selected_variant": 0,
                "approved": False,
                "flagged": False,
                "note": "",
                "animation": anim_for(p.get("shot", "")),
            }
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "episode.json"
    json.dump(out, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"episode.json: {len(out['panels'])} panels -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
