# Interviewer Notes — DO NOT give to the candidate

This assignment mirrors a real product-image syndication problem. The `BRIEF.md` is
**deliberately under-specified**. The point is to see whether the candidate **interrogates the
spec and the data** before coding, and how they handle messy, real-world inputs. A candidate who
silently charges in will hit the landmines; a good one surfaces them and asks.

## The data model (what's actually going on)

- `products.csv` is a 4-level tree via `parent_id` + `level`:
  `master_model ($) → season → article (+) → sku`. **Images belong on the article.**
- Image filenames encode the join info: `DSC_<code>_<view>_<pic>_<name>.png`.
  - `<code>` = the article's base code (article code **without** the trailing `+`).
  - `<view>` = 0,1,2,3,D1,D2 ; `<pic>` = GHO (ghost), MOD (model), PLP (card), BEA (beauty).
  - The mapping addresses images by **slot** = `<view>_<pic>` (e.g. `0_GHO`).
- `mapping.json`: `property → taxonomy → { order:[slots], fallbacks? }`. Properties:
  `main_image` (one image, has fallbacks), `gallery` (ordered set), `plp_cards`, and
  `hero_video` (**null** — must be skipped, not emitted).
- A "good" output: per article, for each property, resolve the mapping's slots against that
  article's images, in order → an import file keyed by the article's `RECORD_ID`.

## Planted landmines (see `_planted_pitfalls.json` for exact ids)

| # | Landmine | What it tests | Good behaviour |
|---|---|---|---|
| 1 | **Case mismatch** — image filename code lowercased vs product code | do they assume exact match? | case-insensitive join, or ask |
| 2 | **Trailing whitespace** in a product code | input hygiene | strip/normalize codes |
| 3 | **`+` / `$` suffixes** — article `+`, model `$` | do they discover the real key? | strip `+`, join on base code |
| 4 | **Zero-padded view** — `01` vs `1` | slot normalization | normalize view tokens |
| 5 | **Multiple images per slot** (a `-alt` duplicate) | ambiguity handling | ask "which wins?"; pick a deterministic rule + state it |
| 6 | **Missing hero view** — only `3_GHO`, mapping wants `0_GHO` | do they use fallbacks? | apply `main_image` fallbacks |
| 7 | **Orphan images** — `ZZ9999*` codes with no product | join direction | drop + report, don't crash |
| 8 | **Articles with zero images** (~15) | empties | emit nothing / handle gracefully |
| 9 | **Non-image files** in `images/` (`.pdf`, `.tif`) | filtering by type | skip non-images; the `.tif` is the "too big to ingest" trap |
| 10 | **Unicode names** (Ümlaut Grün, Beige²) | encoding | UTF-8 throughout |
| 11 | **Mapping typo** — `gallery` tax `200100` has split tokens `"D1","BEA"` instead of `D1_BEA` | do they validate the config? | detect/repair or flag |
| 12 | **Duplicate product row** differing only by case | dedup | dedup, don't double-emit |
| 13 | **Embedded commas** in a product name | CSV correctness | use a real CSV parser, not `split(",")` |
| 14 | **`hero_video: null`** property | don't emit empty props | skip null mapping entries |

## Questions a strong candidate asks (positive signal)

- What's the **match key** between images and products? (base article code)
- What identifies a **slot**, and what's the order/priority?
- **Multiple images for one slot — which wins?** (there is no "right" answer; we want them to
  notice and decide deliberately.)
- What should happen to **images with no matching product**, and **products with no images**?
- What's the **output format / what system consumes it**? (they should ask — the brief hides it)
- Case sensitivity? Whitespace? How strict on the mapping config?
- Do certs/PDFs/TIFs belong here? (no)

## Rubric

- **Junior**: parses the files, joins something, produces output; may miss several landmines but
  handles a few and asks at least one clarifying question.
- **Mid**: real CSV parsing, correct base-code join, applies the mapping + order, filters
  non-images, handles orphans/empties, asks about the ambiguous ones.
- **Senior**: all of the above + treats the spec as untrusted (asks about output/consumer and
  the "which image wins" rule up front), normalizes case/whitespace/zero-pad, validates the
  mapping (catches the split-token typo), makes deterministic choices and **documents the
  decisions + open questions**. Bonus: notes the TIF-ingest and unicode risks unprompted.

## Regenerate / tune

`python3 generate.py` (seed=7, reproducible). Adjust counts, vocab, or which landmines are
active at the top of the script. `_planted_pitfalls.json` is the machine-readable answer key —
**keep it out of the candidate's copy.**
