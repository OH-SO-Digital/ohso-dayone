#!/usr/bin/env python3
"""GOLD reference solver for the ohso-dayone assignment (INTERVIEWER SIDE).

Resolves the dataset the way we consider correct — handling every planted landmine:
  - real CSV parsing (embedded commas), UTF-8
  - article tree; images belong on the article; key = base code (strip '+', whitespace, case-insensitive)
  - slot = <view>_<pic>; normalize zero-padded views (01 -> 1); pic upper-cased
  - skip non-image files (.pdf/.tif); drop orphan images (no product)
  - mapping: skip null properties; repair split-token typos (["D1","BEA"] -> "D1_BEA")
  - main_image capped to 1 with fallbacks; multiple-images-per-slot -> deterministic (sorted, last)
  - dedup case-duplicate product rows
Output: gold_export.csv  (RECORD_ID + property columns; values = image filenames).
"""
import csv, json, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "data", "images")
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")


def norm_code(c):
    return c.strip().rstrip("+").strip().lower()


def norm_view(v):
    return str(int(v)) if v.isdigit() else v      # "01" -> "1"; "D1" stays


def clean_order(order):
    """Repair the split-token typo: consecutive bare tokens -> one slot."""
    out, i = [], 0
    while i < len(order):
        s = order[i]
        if "_" in s:
            out.append(s); i += 1
        elif i + 1 < len(order) and "_" not in order[i + 1]:
            out.append(f"{s}_{order[i+1]}"); i += 2
        else:
            i += 1                                 # unrepairable bare token -> drop
    return out


def load_articles():
    seen, arts = set(), {}
    with open(os.path.join(HERE, "data", "products.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["salsify:data_inheritance_hierarchy_level_id"].strip() != "article":
                continue
            rid = row["RECORD_ID"].strip()
            key = rid.lower()
            if key in seen:                        # dedup case-duplicate rows
                continue
            seen.add(key)
            arts[rid] = {"base": norm_code(row["PRODUCT_CODE"]),
                         "tax": row["TAXONOMY"].strip(),
                         "name": row["ARTICLE_NAME"]}
    return arts


def index_images():
    slots = defaultdict(lambda: defaultdict(list))   # base_code -> slot -> [filename]
    for fn in os.listdir(IMG):
        if not fn.lower().endswith(IMG_EXT):        # skip .pdf/.tif non-images
            continue
        parts = fn.rsplit(".", 1)[0].split("_")
        if len(parts) < 4 or parts[0] != "DSC":
            continue
        base = parts[1].strip().lower()
        view = norm_view(parts[2]); pic = parts[3].upper()
        slots[base][f"{view}_{pic}"].append(fn)
    # deterministic pick when a slot has multiple images: sort, take last (documented rule)
    return {b: {s: sorted(v)[-1] for s, v in d.items()} for b, d in slots.items()}


def main():
    arts = load_articles()
    imgs = index_images()
    mapping = json.load(open(os.path.join(HERE, "data", "mapping.json"), encoding="utf-8"))
    props = [p for p, v in mapping.items() if isinstance(v, dict) and v]   # skip null hero_video

    resolved = {}
    width = {p: 0 for p in props}
    for rid, a in arts.items():
        slots = imgs.get(a["base"], {})
        row = {}
        for p in props:
            rule = mapping[p].get(a["tax"]) or mapping[p].get("default")
            urls = []
            if rule:
                for slot in clean_order(rule.get("order", [])):
                    fn = slots.get(slot)
                    if not fn:
                        for fb in rule.get("fallbacks", {}).get(slot, []):
                            if slots.get(fb):
                                fn = slots[fb]; break
                    if fn and fn not in urls:
                        urls.append(fn)
                    if p == "main_image" and urls:
                        urls = urls[:1]; break
            row[p] = urls
            width[p] = max(width[p], len(urls))
        if any(row.values()):
            resolved[rid] = row

    active = [p for p in props if width[p] > 0]
    header = ["RECORD_ID"] + [p for p in active for _ in range(width[p])]
    with open(os.path.join(HERE, "gold_export.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(header)
        for rid, row in resolved.items():
            cells = []
            for p in active:
                v = row.get(p, [])
                cells += v + [""] * (width[p] - len(v))
            w.writerow([rid] + cells)
    print("gold_export.csv | properties:", {p: width[p] for p in active},
          "| articles with images:", len(resolved), "/", len(arts))


if __name__ == "__main__":
    main()
