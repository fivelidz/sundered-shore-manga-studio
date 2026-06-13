# MANGA STUDIO SYSTEM IMPROVEMENTS — Diagnosis & Fixes

## 1. CRITICAL ISSUES (Ranked by Severity)

### 1.1 MISSING SCRIPT STEP [SEVERITY: CRITICAL]
**Problem:** The entire script-writing phase is absent from the pipeline. Episodes jump directly from prose chapters to visual storyboarding with no dramatic adaptation step.
**Fix:** Insert new Step 2 in pipeline: SCRIPT phase that adapts prose beats into dramatic scenes with dialogue, action beats, and minimal captions.
**Type:** Process + tooling

### 1.2 HARD-CODED EMPTY DIALOGUE [SEVERITY: CRITICAL]
**Problem:** `build_episode.py` line 123 hard-codes `"dialogue": []` for every panel, making dialogue impossible even if written.
**Fix:** Modify build_episode.py to read `dialogue` and `bubbles` arrays from storyboard JSON if present, defaulting to [] for backward compatibility.
**Type:** Code (immediate fix below)

### 1.3 NO SCRIPT SCHEMA [SEVERITY: HIGH]
**Problem:** No defined JSON schema for scripts/storyboards to carry dialogue data into the build process.
**Fix:** Define schema where each panel can include:
```json
{
  "dialogue": [
    {
      "type": "speech|thought|caption|sfx",
      "speaker": "Character name",
      "text": "The actual line",
      "anchor": "top-left|top-right|bottom-left|bottom-right|center|auto"
    }
  ],
  "bubbles": [
    {
      "type": "speech|thought|caption",
      "anchor": "position for blank bubble rendering"
    }
  ]
}
```
**Type:** Schema definition + documentation

### 1.4 NO CHARACTER CONTINUITY MECHANISM [SEVERITY: HIGH]
**Problem:** No system to track character voice consistency, relationships, or knowledge state across episodes. Each episode risks character drift.
**Fix:** Create a character continuity JSON that tracks:
- Voice register per character (technique_library references)
- What each character knows at each episode boundary
- Relationships/tensions that must carry forward
- Physical continuity (injuries, possessions)
**Type:** Process + new continuity file per arc

### 1.5 LETTERING SYSTEM NOT BUILT [SEVERITY: MEDIUM]
**Problem:** The "second pass lettering" system exists in concept but has no implementation. Blank bubbles would render, but text composite step is missing.
**Fix:** Build compositing script that:
1. Reads episode.json panel.dialogue[]
2. Overlays text onto blank bubble regions
3. Handles font, size, positioning per type (speech/thought/caption)
**Type:** Code (new script needed)

### 1.6 NO DRAMATIC CONFLICT VALIDATION [SEVERITY: MEDIUM]
**Problem:** No automated check for whether episodes contain actual dramatic conflict (two-handers, opposing wants) vs flat narration.
**Fix:** Add validation step that checks each episode for:
- At least one dialogue exchange between characters
- Caption ratio ≤ 1 per 3 panels
- Variety in dialogue types (not all captions)
**Type:** Code (validation script)

### 1.7 PROSE LIFTING WITHOUT ADAPTATION [SEVERITY: MEDIUM]
**Problem:** Current captions are verbatim prose sentences, not adapted for visual medium. Interior monologue doesn't translate to panels.
**Fix:** Script step must transform prose interiority into:
- Spoken dialogue (primary)
- Visual action (shown not narrated)
- Rare captions (only for unreachable interiority)
**Type:** Process (part of script step)

## 2. THE SCRIPT SCHEMA (Detailed)

Each storyboard panel in the source JSON can now carry:

```json
{
  "panel": 7,
  "shot": "medium_two_shot",
  "aspect": "2:3",
  "prompt": "Panel visual prompt...",
  "dialogue": [
    {
      "type": "speech",        // speech|thought|caption|sfx
      "speaker": "Aldric",     // Character name (empty for sfx/some captions)
      "text": "Collect the dry brush. The brown, not the green.",
      "anchor": "top-left"     // Positioning hint for lettering
    },
    {
      "type": "thought",
      "speaker": "Cael",
      "text": "He ranks the tasks. He can't do any of them.",
      "anchor": "bottom-right"
    }
  ],
  "bubbles": [
    {
      "type": "speech",
      "anchor": "top-left"
    },
    {
      "type": "thought",
      "anchor": "bottom-right"
    }
  ],
  "caption": "",  // DEPRECATED - use dialogue with type:"caption" instead
  "caption_pov": ""  // DEPRECATED
}
```

## 3. CODE FIX IMPLEMENTATION

### build_episode.py modification (line ~120-125):
**Current (broken):**
```python
"dialogue": [],  # Hard-coded empty
"bubbles": [],   # Hard-coded empty
```

**Fixed (reads from storyboard):**
```python
# Read dialogue and bubbles from storyboard if present, else default to []
"dialogue": p.get("dialogue", []),
"bubbles": p.get("bubbles", []),
```

The build script now also accepts EITHER a bare list of panels (legacy storyboards)
OR a script-wrapper object `{"panels": [...], "_script": ...}` so the SCRIPT step can
carry top-level metadata. Both forms produce identical episode.json output.

### Editor Compatibility:
The editor (editor.js) expects these exact fields:
- `dialogue[]` array with objects containing: `type`, `speaker`, `text`, `anchor`
- Types must be from: `['speech', 'thought', 'caption', 'sfx']`
- This matches our schema exactly — no field name changes needed.

## 4. IMMEDIATE ACTIONS

1. **Backup build_episode.py** → build_episode.py.bak ✓
2. **Modify build_episode.py** to read dialogue/bubbles from storyboard ✓
3. **Create demo script** for A1E01 panels 1-8 with real dialogue ✓
4. **Document the schema** in this file ✓
5. **Test the pipeline** with the demo script

The key insight: the editor already supports dialogue display/editing. The build script was the bottleneck, hard-coding empty arrays. One small code change unblocks the entire dramatic adaptation system.

## 5. RESOLUTION STATUS (this session)

| Issue | Status | Component |
|-------|--------|-----------|
| 1.1 Missing SCRIPT step | ✅ RESOLVED | doctrine + demo + validator enforce it |
| 1.2 Hard-coded empty dialogue | ✅ RESOLVED | `build_episode.py` reads `dialogue[]`/`bubbles[]` |
| 1.3 No script schema | ✅ RESOLVED | schema documented §2; editor-compatible |
| 1.4 No character continuity | ✅ RESOLVED | `continuity/characters.json` (appearance lock, single source) + `continuity/arc1_state.json` (cross-episode memory); `build_episode.py` builds cast block from it |
| 1.5 Lettering not built | ✅ RESOLVED | `scripts/letter_episode.py` (PIL bubbles + text → `lettered/`) |
| 1.6 No conflict validation | ✅ RESOLVED | `scripts/validate_episode.py` (M001–M007 checks, exit 1 blocks ship) |
| 1.7 Prose-lifting w/o adaptation | ✅ RESOLVED | script step + caption-budget check |
| Feedback loop (review→improve) | ✅ RESOLVED | `render_episode.py --regen` maps reject notes → prompt fixes |
| Manga failure registry | ✅ ADDED | `MANGA_FAILURE_REGISTRY.md` (M001–M008) |

### Art consistency — honest note
Consistency is now (a) a single-source appearance lock injected into every multi-character
prompt and (b) a regen fix when "wrong character" is flagged. True pixel-level face locking
(IP-Adapter / reference-image img2img) is scaffolded — `ref_images: []` slots exist per
character in `characters.json` — but the img2img render path is NOT yet wired. That is the
one remaining consistency upgrade. Everything else the original spec asked for is built.