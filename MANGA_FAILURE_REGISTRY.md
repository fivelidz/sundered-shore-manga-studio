# Manga Failure Registry — every caught adaptation mistake, in checkable form

> The manga analogue of the novel's `failure_registry.md`. Every fault the user catches in
> a rendered/scripted episode becomes a permanent, specific, CHECKABLE entry here. Before
> shipping any episode, run the validator (`scripts/validate_episode.py`) and red-team the
> script against EVERY entry. Append new failures; never delete or soften one.
>
> Format per entry: ID + name · CAUGHT (the rejected thing) · WHY IT FAILS · THE RULE ·
> CHECK (the concrete test, automated where possible).

---

## M001 — Narration-only episode (zero spoken dialogue)
- **CAUGHT:** A1E01 (Ch1) shipped with 35 panels, all carrying narration captions lifted
  verbatim from the prose. No character spoke to another anywhere. User: *"horrifically
  bad... lacks any interesting detail."*
- **WHY IT FAILS:** Manga is a dramatic medium; narration-over-pictures is its weakest tool.
  Interiority that works in 4-POV prose reads flat and lifeless floating over panels.
- **THE RULE:** Every episode is SCRIPTED into spoken drama + action first. Captions are
  seasoning, not the meal.
- **CHECK (automated):** `validate_episode.py` — episode must contain ≥1 `speech` entry and
  a caption ratio ≤ ~1 per 3 panels.

## M002 — Caption budget blown
- **CAUGHT:** Same episode — caption on nearly every panel.
- **WHY IT FAILS:** Captions narrate what the art + dialogue should carry; they release the
  reader from doing the work (the cardinal rule: the reader supplies the response).
- **THE RULE:** Caption budget ≤ ~1 per 3 panels, only for interiority no line/action can
  carry (a number Signe verifies; a thing Marit notices but would never say aloud).
- **CHECK (automated):** captions / panels ≤ 0.34.

## M003 — Hard-coded empty dialogue (pipeline bug)
- **CAUGHT:** `build_episode.py` wrote `"dialogue": []` for every panel; the script step's
  output could never reach the episode.
- **WHY IT FAILS:** The data path for drama did not exist, so no amount of scripting helped.
- **THE RULE:** `build_episode.py` reads `dialogue[]`/`bubbles[]` from the storyboard.
- **CHECK:** A storyboard with dialogue produces an episode.json whose panels carry it.

## M004 — No spoken two-hander (no conflict)
- **CAUGHT:** Arc I episodes risk being a sequence of events with no one wanting opposing
  things aloud (the W1 prose weakness inherited).
- **WHY IT FAILS:** Drama is people wanting different things and saying so. Without it the
  episode is a slideshow.
- **THE RULE:** ≥1 two-hander per episode where two leads want different things and argue it
  (Aldric vs Cael E1; Signe vs Marit E2; etc. — see `ADAPTATION_DOCTRINE_arc1.md`).
- **CHECK (automated, advisory):** ≥2 distinct named `speech` speakers in the episode.

## M005 — Mystical awe instead of grounded uncanny
- **CAUGHT (preventive):** "eyes of fire / gods from the sun" framing for first contact.
- **WHY IT FAILS:** The whole world-premise is that awe is a MISREADING of technology by
  intelligent people. Mysticism throws away the theme.
- **THE RULE:** Terror is built from REAL objects (the reflective sunglasses that erase the
  eyes; the too-bright blade; skin that burns; numbers-speech). The reader supplies the dread.
- **CHECK:** scan dialogue/captions for banned mystical vocab (god, divine, glowing eyes,
  magic, sun-god) in any awe beat.

## M006 — Twist-gate breach (multiverse language in Arc I)
- **CAUGHT (preventive):** "the Commonality / parallel timeline / other world" leaking into
  early dialogue.
- **WHY IT FAILS:** The divergent-timeline reveal is mid-arc; early language must read as
  future-humans → empty world.
- **THE RULE:** No multiverse/divergent-timeline vocabulary in Arc I scripts.
- **CHECK (automated, advisory):** scan for {multiverse, parallel timeline, the Commonality,
  world-walk, divergent}.

## M007 — Dimmed restraint broken (narrating the injustice)
- **CAUGHT (preventive):** a line/caption that pities or editorialises the Dimmed's
  exploitation ("it wasn't fair that…", "nobody thanked her, and that was wrong").
- **WHY IT FAILS:** Same as the prose: the moment the page supplies the outrage, the reader
  is released from supplying it. Show competence as fact; MOVE.
- **THE RULE:** Dimmed competence is shown and the scene moves; no one on the page narrates
  the pity or the injustice. ("None of us asked her to." is the ceiling — fact, not verdict.)
- **CHECK:** red-team any Dimmed beat for editorialising verbs (deserved, unfair, exploited,
  pitied).

## M008 — Character look drift across panels/episodes
- **CAUGHT (preventive):** a lead rendered with the wrong hair/props so the reader can't
  track who is who.
- **WHY IT FAILS:** Breaks the reader's grip on the cast; the user's feedback #1.
- **THE RULE:** Appearance is locked ONCE in `continuity/characters.json` and injected into
  every multi-character prompt; flagged drift regenerates with the cast-lock fix (M004 loop).
- **CHECK:** `validate_episode.py` confirms multi-character panels carry the CAST block;
  reject-with-reason "wrong character" feeds the regen fix.

---

## Red-team checklist (run before shipping an episode)
1. ≥1 spoken `speech` line? (M001)
2. Caption ratio ≤ 1/3 panels? (M002)
3. dialogue[] actually present in episode.json? (M003)
4. ≥1 two-hander, ≥2 named speakers? (M004)
5. Any awe grounded in real objects, never mysticism? (M005)
6. No multiverse language in Arc I? (M006)
7. No narrated pity/injustice for the Dimmed? (M007)
8. Multi-character panels carry the cast-lock block? (M008)
