# Manga Studio — build-out prompts for a fresh session

> Copy-paste one block into a new agent session to continue this system. Each is
> self-contained: context pointer + task + acceptance test. Read `README.md` first in
> every case. The meta-goal: not just making this story's manga — building a SYSTEM
> that turns any prose + prompts into reviewed, lettered, animatable visual chapters.

---

## P1 — Second-pass lettering compositor
```
Read ~/projects/manga_studio/README.md. Build the lettering pass: a script
(scripts/letter_episode.py, PIL) that takes episode.json and, for each APPROVED panel
with dialogue[], composites the text over the image: speech/thought/caption styles per
editor.css POV colours, auto-wrapped, anchored by dialogue[].anchor (add an anchor
picker to the editor: tap position on the image -> stores {x%, y%}). Output to
renders_lettered/. Acceptance: one lettered panel renders with readable text in a
clean bubble shape; editor gains a "lettered preview" toggle; no text is ever sent to
the image model.
```

## P2 — Flag-driven regeneration loop
```
Read ~/projects/manga_studio/README.md + scripts/render_episode.py. Build
scripts/regen_flagged.py: for each FLAGGED panel, construct an improved prompt (apply
the panel's note: e.g. "hands/fingers" -> add hand-fix language; "wrong character look"
-> re-paste that character's lock + CAST DIFFERENTIATION), render 2 fresh variants,
append, clear the flag but keep the note as history[]. Acceptance: flag a panel with a
note in the editor, run the script, see 2 new variants in the chooser.
```

## P3 — Character visual consistency (the hard one)
```
Read ~/projects/manga_studio/README.md. The leads drift between panels (schnell).
Investigate and implement the best consistency lever available on Replicate today:
character reference images (generate ONE canonical portrait per lead from the style
bible locks, then use an image-conditioning model — flux-redux / IP-adapter-style / a
LoRA if trainable) so every panel conditions on the canonical face. Wire it as an
optional --char-ref mode in render_episode.py. Acceptance: re-render 3 panels of Signe
with refs; faces match the canonical portrait recognisably.
```

## P4 — Episodes 2–6 production run (Arc I complete)
```
Read story_mode/projects/the-sundered-shore/06_image_prompts/manga_production_plan.md
(§3 directives) + the A1E01 storyboard JSON as the format reference. For each of Ch2-6:
spawn an Opus storyboard sub-agent (30-40 panels from the 4 POV files), build_episode.py,
render 3 variants (systemd-run unit, resumable), verify in the editor API. Acceptance:
/api/episodes lists a1e02..a1e06 with full renders; production plan §5 table updated.
```

## P5 — Animation / video-AI export
```
Read ~/projects/manga_studio/README.md (§animation-ready). Build
scripts/export_shotlist.py: episode.json -> (a) a generic shot-list JSON (image path,
camera, motion_hint, duration, transition, dialogue-as-subtitles) and (b) one concrete
adapter (e.g. Replicate's stable-video-diffusion or kling/wan img2video if available):
render panel 1-3 of A1E01 into short clips. Acceptance: 3 clips exist; shotlist
validates against approved panels only.
```

## P6 — Ship approved episodes to the story reader
```
Read ~/projects/manga_studio/README.md + story_mode/scripts/seed_v4b_survival.py (comic
ingest block). Build the bridge: an exporter that takes an episode with >=80% approved
panels and writes a reader-format prompts JSON (selected variant as render_uri, captions)
into story_mode's image-prompts dir + copies finals to app/reader/comic/, then reseeds a
fresh root and relaunches the phone-reader unit (systemd-run, NEW unit name, then pkill
old). Acceptance: phone reader's comic view shows the approved A1E01 panels in order.
```

## P7 — Editor UX round 2
```
Read editor/editor.js. Add: (a) keyboard nav (j/k panel, 1/2/3 variant, a approve,
f flag); (b) filter bar (all / flagged / unapproved / no-variants); (c) bulk approve;
(d) a compare mode showing all 3 variants side-by-side inline; (e) bubble-slot editor
(add speech/thought/caption slot with anchor; feeds render-time blank bubbles).
Acceptance: all five work on phone-width viewport; state survives reload.
```

## Known constraints (do not relearn these)
- Background processes get REAPED: always `systemd-run --user --unit <fresh-name>`.
- FLUX letters text badly: images stay text-free; bubbles render BLANK.
- Replicate throttle ~6/min on this account: keep the 11s pacing.
- Editor server: real 302 redirect for "/" (relative-asset 404 bug, already fixed).
- Archive before overwrite; never delete; record user prompts verbatim in
  story_mode/projects/the-sundered-shore/00_brief/user_prompts_verbatim.md.
