# MANGA STUDIO — generation + review + lettering pipeline (standalone project)

> **Location: `/home/fivelidz/projects/manga_studio/`** — its own project, separate from
> the novel repo. Adapts *The Sundered Shore* (and any future story) into phone-scrollable
> manhwa with an AI-fault review workflow. Inspiration register: isekai + survival manga
> (Dr. Stone, Vinland Saga, Sōsei no Taiga): competence beats, nature-as-antagonist,
> knowledge inserts the reader actually learns from.

---

## WHERE EVERYTHING IS (the locations table)

| Thing | Location |
|-------|----------|
| **This project root** | `/home/fivelidz/projects/manga_studio/` |
| **The editor UI** (desktop browser app) | `editor/` (index.html / editor.js / editor.css) |
| **The phone reviewer** (installable PWA) | `editor/phone/` (index.html / phone.js / phone.css / sw.js / manifest) |
| **Editor server** | `scripts/editor_server.py` (port **2910**) — serves both |
| **Episode content** | `episodes/<episode_id>/` — one folder per episode |
| **Episode master file** | `episodes/a1e01_ch01/episode.json` (state: variants, approvals, flags, notes, dialogue, animation hints) |
| **Rendered images** | `episodes/a1e01_ch01/renders/panel_NN_vK.webp` (N=panel, K=variant 1–3) |
| **Renderer** | `scripts/render_episode.py` (Replicate FLUX; progress-safe; resumable; `--regen` reads reject notes → prompt fixes) |
| **Episode builder** | `scripts/build_episode.py` (storyboard JSON → episode.json; reads `dialogue[]`; cast block from continuity) |
| **Lettering compositor** | `scripts/letter_episode.py` (PIL: bakes `dialogue[]` into bubbles → `episodes/<id>/lettered/`) |
| **Episode validator** | `scripts/validate_episode.py` (red-team: blocks narration-only/flat episodes) |
| **Character + continuity** | `continuity/characters.json` (appearance source-of-truth) · `continuity/arc1_state.json` (cross-episode memory) |
| **Manga failure registry** | `MANGA_FAILURE_REGISTRY.md` (M001–M008 checkable adaptation rules) |
| **Source storyboards** (novel repo) | `~/projects/Knowledge_systems/story_mode/projects/the-sundered-shore/06_image_prompts/webcomic_v4b_a1e01_ch01_prompts.json` |
| **Style bible** (novel repo) | `.../06_image_prompts/webcomic_style_bible.md` |
| **Production plan / arcs** (novel repo) | `.../06_image_prompts/manga_production_plan.md` |
| **OLD panels** (v4a arrest 42 + v4b covers 5, pre-QA, known AI faults) | `~/projects/Knowledge_systems/story_mode/app/reader/comic/` |

## RUN IT

```bash
cd ~/projects/manga_studio
# the editor (review + approve + select variants):
python3 scripts/editor_server.py --port 2910
#   desktop:  http://localhost:2910/
#   phone  :  http://100.73.134.20:2910/   (Tailscale)

# render variants (resumable; renders v1 of every panel first, then v2, then v3):
python3 scripts/render_episode.py episodes/a1e01_ch01 --variants 3
```

### Phone reviewer (installable PWA)

```
http://localhost:2910/phone           desktop test
http://100.73.134.20:2910/phone       phone (Tailscale)
```
On the phone, open that URL → tap the browser "Add to Home Screen" (or the in-app
**Install** button on Android/Chrome). It launches fullscreen like a native app.
One-thumb review: filter pills (Unreviewed / All / Flagged / Approved), tap an image
to **swipe between the 3 variants** and pick the best, big **✓ Approve / ⚑ Reject**
buttons, reject-reason chips + free text (feeds the regen prompt fix), pull-to-refresh
for newly rendered variants. Autosaves to the same `episode.json` the desktop editor
uses — the two stay in sync.

## THE WORKFLOW (interaction + editing)

> ⚠️ **READ `ADAPTATION_DOCTRINE.md` FIRST.** A1E01 shipped with ZERO dialogue (35 lifted
> narration captions) and read flat/lifeless. The missing piece was a **SCRIPT step**: adapt
> each beat into SPOKEN drama + sparse captions before storyboarding. `build_episode.py` now
> carries `panel.dialogue[]` from the storyboard (was hard-coded empty). Proof-of-fix:
> `episodes/a1e01_ch01/script_demo_p1-8.json`.

0. **SCRIPT** (NEW — the missing step): adapt the chapter's beats into spoken dialogue +
   action + rare captions, in each character's technique-library voice, with a two-hander
   argument per episode. Caption budget ≤ ~1 per 3 panels. See `ADAPTATION_DOCTRINE.md` §3.
1. **Storyboard** (novel repo): Opus agent adapts the SCRIPT → 30-45 panel prompts
   JSON, arc-labeled (`manga_production_plan.md` §3 directives: follow the prose, character
   locks verbatim, twist-gate, knowledge inserts). Each panel may carry a `dialogue[]` array
   ({type, speaker, text, anchor}) which `build_episode.py` reads through.
2. **Build**: `build_episode.py` → `episode.json`. Injects the **CAST DIFFERENTIATION**
   block (each lead visually distinct: Signe braid / Aldric tallest+blade / Cael tousled+case /
   Marit honey hair+notebook) and animation defaults.
3. **Render**: 3 variants per panel, variant-pass-major (full readthrough fast). FLUX
   **letters text badly — so generation is text-free.** Bubbles, if requested per panel,
   render BLANK (empty speech/thought/caption shapes, no letters).
4. **Review in the editor** (the AI-fault workflow):
   - scroll the episode like a manhwa on the phone;
   - **click an image** → see all 3 generations → pick the best;
   - **approve ✓** good panels; **flag ⚑** faulty ones with a **note** (quick fault chips:
     hands/fingers, face drift, wrong character look, text artifact, palette, anatomy);
   - dialogue/captions appear **UNDER the image** (POV colour-coded) during review.
5. **Regenerate flagged**: re-run the renderer — flagged panels get fresh variants appended
   (notes feed prompt fixes).
5b. **Regenerate flagged with FIX** (feedback loop): `render_episode.py --regen` reads each
   flagged panel's reject note, maps the fault (hands / face drift / wrong character /
   palette / etc.) to a corrective prompt phrase, appends a fresh variant, selects it, and
   clears the flag so it re-enters review. Review → improve is now closed.
6. **SECOND-PASS LETTERING** (built): `letter_episode.py` bakes `panel.dialogue[]`
   (speech/thought/caption/sfx, speaker, text, anchor) onto the chosen variant with PIL —
   drawn bubbles + crisp text, never generated by FLUX. Output: `lettered/panel_NN.webp`.
   Default letters approved panels; `--all` or `--panels 1,2,7` to target.
7. **VALIDATE + Ship**: `validate_episode.py --arc1` enforces the failure registry
   (≥1 spoken line, caption ratio ≤ 1/3, ≥2 speakers, no mysticism/twist-gate/Dimmed-pity).
   Exit 0 → approved lettered panels flow back into the story reader.

### The full corrected pipeline (one line)
```
SCRIPT → build_episode → render (3 variants) → review (phone/desktop) →
  --regen flagged with note-fix → letter_episode → validate_episode → ship
```

## THE JSON IS ANIMATION-READY

`episode.json` carries per panel: `animation: {camera, motion_hint, duration_s, transition}`
plus prompt/negative/caption/dialogue — directly usable as a shot-list for video-AI
(Runway/Kling/Veo-style img2video: image = the approved variant, motion = `motion_hint`,
camera = `camera`, clip length = `duration_s`). Export via the editor's ⬇ JSON button.

## STATUS / VERSIONS

| Episode | Panels | State |
|---------|--------|-------|
| **a1e01_ch01** — ARC I "The Crossing" E1 | 35 | storyboarded ✓ · rendering 3×35=105 imgs (in progress) · review OPEN |
| a1e02–a1e06 (Arc I) | — | queued (storyboard next) |
| OLD: v4a arrest ch (42), v4b covers (5) | 47 | pre-QA legacy, known AI faults, kept for comparison |
