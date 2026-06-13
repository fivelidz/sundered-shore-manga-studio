# ARC I — THE CROSSING · Episode Script Plan (A1E01–A1E06)

> §5 of the Adaptation Doctrine. The DRAMATIC spine of each Arc I episode: the conflict,
> the two-hander argument, the spoken turn, and how captions are demoted to seasoning.
> Source chapters: v4b survival Ch1–6. Panel counts per `manga_production_plan.md`.
> Each episode MUST be SCRIPTED (dialogue written) before storyboarding — see §2 doctrine.

---

## A1E01 — The Crossing (Ch1) · ~35 panels · REBUILD NEEDED

**Current state: BROKEN — 0 dialogue, 35 narration captions.** Re-script before re-render.

- **What happens:** five Regnant + three Dimmed arrive on the empty plateau, crossing-sick,
  in punishing sun. They cannot do basic things; Brenn (Dimmed) makes fire while Aldric
  fails. The first competence-inversion lands.
- **The drama to ADD (currently absent):**
  - **Two-hander:** Aldric vs Cael, spoken — Aldric ordering the group into a priority
    order while Cael, hands over his eyes, needles him ("You can rank the tasks. You can't
    do any of them."). Status contest, light, real.
  - **The set-piece as ACTION not caption:** Aldric striking sparks, failing; Brenn lighting
    it in silence. Let it play in panels with maybe ONE Cael line ("He went to work. We went
    to university.") — spoken, not narrated.
  - **Signe** gets ONE caption (the water arithmetic / the error-log decision — interiority
    only she can carry). Everything else becomes speech or action.
- **Caption budget:** ≤ 4 (down from 35). The rest → dialogue + action.
- **Decision staged (light):** who leads? Aldric assumes it; nobody quite agrees. Seed.

## A1E02 — The Spring (Ch2) · ~32 panels

- **What happens:** the descent to the spring; Cael's fall on wet karst; first water secured.
- **Drama:** **Signe vs Marit** two-hander on the ledge — Signe wants the measured safe route,
  Marit found the spring by EAR and wants to trust the world's signals. Method clash
  (data vs attention) spoken aloud. Cael's fall is pure action + a wry line at the bottom.
- **Knowledge insert (as dialogue, not lecture):** the litres-per-day math delivered as
  Signe correcting someone, not as a caption essay.

## A1E03 — First Night (Ch3) · ~32 panels

- **What happens:** dark, cold, a predator-fear night; the group's competence gaps at night.
- **Drama:** **Aldric vs Signe** — ration the fire/water now vs trust tomorrow's yield. The
  first real resource-authority argument (prefigures the later power-budget node).
- **FIX the Ch3 redundancy the prose audit caught:** do NOT give every character the same
  "47% confidence" fear-beat. ONE character voices the Oracle's confidence number; the
  others react in their own register (Cael's body, Marit's curiosity, Aldric's command).

## A1E04 — Ysel's Domain (Ch4) · ~34 panels

- **What happens:** Ysel (Dimmed) quietly runs the camp's food/water competence; the leads
  depend on her without acknowledging it.
- **Drama:** the Dimmed restraint is the whole episode. **Show** Ysel's competence as fact;
  the ONE moment of weight is Signe's caption "None of us asked her to." — kept. The
  argument here is internal to the leads (Marit notices the dependency; Aldric files it as
  an asset) — a short Marit-vs-Aldric exchange about what Ysel IS to them.

## A1E05 — Triage (Ch5) · ~34 panels

- **What happens:** an injury/illness forces a triage decision; Signe overrides the Oracle.
- **Drama:** **Signe vs Aldric** — her medical authority vs his command authority, spoken,
  tense. This is the episode's spine and it is already latent in the prose; put it in
  bubbles. The knowledge insert (triage logic) is delivered THROUGH the argument.

## A1E06 — First Contact (Ch6) · ~45–55 panels · ARC PEAK

- **What happens:** the first Bronze-Age locals. The Regnant are seen. **NODE A fires**
  (commit to Earth / retreat / supply-run only) — stage it OPEN.
- **Drama + the SUNGLASSES directive (see doctrine §4):** the locals' terror is built from
  REAL objects — the reflective lenses that erase the strangers' eyes, the skin that does
  not tan, the too-bright blade, the numbers-speech. NO mystical "eyes of the sun" framing.
- **Two-hander:** **Marit vs Aldric** — Marit wants to be SEEN as people and make contact
  on the locals' terms; Aldric wants to manage the perception as leverage ("Let them think
  what frightens them most usefully."). The theme (who counts as us / gods vs people)
  enters as ARGUMENT, the reader picks.
- **Decision NODE A staged on the page, left open.**

---

## PRODUCTION ORDER

1. **Re-script A1E01** (highest priority — it is the broken reference everyone judges).
2. Script A1E02–A1E05 from the chapters (drama spine above).
3. Script + storyboard **A1E06** with the sunglasses first-contact as the arc-peak payoff.
4. `build_episode.py` change: read a `dialogue` array from the storyboard JSON into
   `panel.dialogue[]` instead of hard-coding `[]`. (Small code change; unblocks everything.)
5. Render → review gate per episode → letter → ship.

**Acceptance test per episode:** does it contain at least one spoken two-hander argument?
Is the caption count ≤ ~1 per 3 panels? Is every line sayable by only that character? Is
any awe grounded in a real object (never mysticism)? If no → not done.
