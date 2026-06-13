# MANGA ADAPTATION DOCTRINE — the missing SCRIPT step, and the arc-coherent plan

> Written after user review of A1E01 (Ch1): *"The dialogue in the manga is horrifically
> bad... it all seemed to lack any interesting detail."* The diagnosis below is the
> controlling reason this doc exists. Read it before storyboarding ANY episode.

---

## 1. THE DIAGNOSIS (what actually went wrong in A1E01)

**A1E01 has ZERO spoken dialogue.** All 35 panels carry **narration captions** — prose
sentences lifted verbatim from the chapter (Signe's interior log, Cael's asides, Marit's
notebook). No character speaks to another character anywhere in the episode.

In the novel that interiority works (it is the four-POV instrument). Pasted onto manga
panels as floating narration it reads **flat, talky, and lifeless**, because:

1. **Manga is a DRAMATIC medium.** Its native unit is people doing and saying things to
   each other. Narration-over-pictures is the weakest tool in the form; we used ONLY it.
2. **The build pipeline never writes dialogue.** `build_episode.py` hard-codes
   `"dialogue": []`. The "second-pass lettering" was designed to *place* dialogue — but
   no step was ever built to *write* it. The script step is missing from the whole system.
3. **This is the same W1 weakness the prose critique already flagged** ("characters don't
   talk to each other enough"). The comic inherited it and made it impossible to hide.

**So the fix is not "rewrite the captions." It is: add the SCRIPT step that the pipeline
never had — adapt each beat into spoken drama, and demote captions to a rare seasoning.**

---

## 2. THE CORRECTED PIPELINE (the SCRIPT step is new — step 2)

```
1. BEAT SHEET     From the arc design: what HAPPENS, the conflict, the decision/turn.
2. SCRIPT  ← NEW  Adapt each beat into a SCENE: spoken dialogue + action + (rare) caption.
                  Dialogue in each character's technique-library voice. The DRAMA on the page.
3. STORYBOARD     Break the script into panels/shots (the existing prompt JSON), now
                  driven by the script: panels exist to carry lines + actions, not prose.
4. BUILD          build_episode.py — now POPULATES panel.dialogue[] from the script.
5. RENDER         FLUX, text-free, 3 variants. (unchanged, works)
6. REVIEW/REGEN   editor :2910 — approve/flag/note, regen flagged. (unchanged, works)
7. LETTER         composite dialogue into blank bubbles. (planned P1)
8. SHIP           approved panels + lettered dialogue back to the reader.
```

The single change that fixes the user's complaint: **insert step 2, and make step 4 read
its output.** Everything downstream already works.

---

## 3. THE DIALOGUE RULES (so the script is not "stupid" or detail-less)

Same doctrine as the prose, applied to speech:

- **Show, don't narrate.** If a caption explains a feeling, find the LINE or ACTION that
  makes the reader feel it instead. Cut the caption.
- **Caption budget: max ~1 per 3 panels**, and only for what ONLY interiority can carry
  (a number Signe verifies; a thing Marit notices that she would never say aloud). Default
  to dialogue + action.
- **Voice on the page.** Every line must be sayable ONLY by that character. Use the
  technique-library voices: Aldric = clipped ledger/command; Signe = precise, dry,
  correcting; Marit = curious, oblique, the strange question; Cael = wry, appetite, the
  body. The Dimmed speak rarely and concretely (Brenn: instructions, never complaint).
- **Concrete > mystical, ALWAYS (the user's cardinal manga note).** Never "eyes of fire,"
  "gods from the sun." Use the GROUNDED uncanny: the sunglasses, the too-bright blade, the
  pale skin that does not burn the way theirs does, the voice that says numbers. Terror
  should be a real cognitive-historical reaction to a specific object, not vague awe.
- **Conflict in every episode.** At least one two-hander where two leads WANT different
  things and say so. This is the W1 fix; the comic is where it is most visible.
- **The Dimmed restraint holds.** Their competence is shown and the scene MOVES; nobody
  on the page narrates the injustice. (Same rule as the novel.)
- **Twist-gate.** No multiverse / divergent-timeline language in Arc I dialogue.

---

## 4. THE SUNGLASSES DIRECTIVE (recorded as canon, user request)

When the Regnant first meet Bronze-Age locals (Ch6 / A1E06, first contact — NOT Ch1), the
locals' terror must be **grounded and specific**, built from real objects:

- **Sunglasses / reflective lenses** worn by the pale strangers — eyes erased, replaced by
  two mirrors that show the watcher his own face. To a Late-Bronze-Age agriculturalist who
  has never seen a flat mirror, a person with no eyes, only reflections, is an
  ontological horror, not a curiosity. THIS is the "eyes" image done right.
- Reinforcing concrete uncanny: skin that burns and peels where theirs tans; a blade with a
  brightness that is fractionally wrong; speech full of exact numbers; the way they do not
  flinch at things that should frighten a person.
- **Hard ban:** no "eyes in the sun," no "gods of light," no glowing/mystical framing. The
  whole point of the world is that the awe is a MISREADING of technology by intelligent
  people — render the misreading from real objects, and let the reader supply the dread.

This belongs in the A1E06 script and in the Ch6 prose first-contact beat. Cross-ref:
`failure_registry` F009 (no naming the abstraction) and the theme spine (reader supplies it).

---

*(continued in §5 — the Arc I episode plan — see ADAPTATION_DOCTRINE_arc1.md)*
