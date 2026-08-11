#!/usr/bin/env python3
"""Validator for a candidate submission (INTERVIEWER SIDE).

Usage:  python3 validate.py <candidate_export.csv>

Checks the candidate's import file against the data + the gold solution and prints a
per-check OK / WARN / FAIL report plus a score. Designed to be lenient on FORMAT (candidates
may key differently or output URLs vs filenames) but strict on the LANDMINES.
"""
import csv, json, os, sys, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "data", "images")

def basename(v):
    v = v.strip().split("?")[0].replace("\\", "/").rstrip("/")
    return v.split("/")[-1]

def real_articles():
    arts = {}
    with open(os.path.join(HERE, "data", "products.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lvl = row["level"].strip()
            arts.setdefault(row["RECORD_ID"].strip().lower(), lvl)
    return arts

def load_export(path):
    """-> {rid: {prop: [basenames...]}} ; property = column header (repeats merged)."""
    out = defaultdict(lambda: defaultdict(list))
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f); h = next(r)
        idcol = 0
        for i, c in enumerate(h):
            if c.strip().lower() in ("record_id", "id"):
                idcol = i; break
        for row in r:
            if not row or not row[idcol].strip():
                continue
            rid = row[idcol].strip()
            for i, c in enumerate(h):
                if i == idcol:
                    continue
                if i < len(row) and row[i].strip():
                    out[rid][c.strip()].append(basename(row[i]))
    return out, h

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 validate.py <candidate_export.csv>")
    cand, header = load_export(sys.argv[1])
    arts = real_articles()
    img_files = set(os.listdir(IMG))
    gold, _ = load_export(os.path.join(HERE, "gold_export.csv"))

    P = lambda tag, ok, msg: print(f"  [{'OK ' if ok=='ok' else ('WARN' if ok=='warn' else 'FAIL')}] {tag}: {msg}")
    score = 0; total = 0
    def check(tag, cond, good, bad, warn=False):
        nonlocal score, total
        total += 1
        if cond: score += 1; P(tag, "ok", good)
        else: P(tag, "warn" if warn else "fail", bad)

    print(f"== validating {os.path.basename(sys.argv[1])} ==")
    print(f"   rows(articles): {len(cand)} | columns: {header}")

    # 1. keys are real ARTICLE records
    bad_ids = [r for r in cand if arts.get(r.lower()) != "article"]
    check("real-article-keys", not bad_ids,
          "all RECORD_IDs are real article records",
          f"{len(bad_ids)} keys are not articles (orphan/sku/model/unknown), e.g. {bad_ids[:3]}")

    # 2. no duplicate rows / case-dup
    seen = defaultdict(int)
    for r in cand: seen[r.lower()] += 1
    dups = [k for k, n in seen.items() if n > 1]
    check("no-duplicate-keys", not dups, "no duplicate RECORD_IDs",
          f"duplicate keys: {dups[:3]}")

    # 3. referenced files exist and are images
    refs = [b for v in cand.values() for lst in v.values() for b in lst]
    missing = [b for b in refs if b not in img_files]
    nonimg = [b for b in refs if b.lower().endswith((".pdf", ".tif", ".tiff"))]
    orphan = [b for b in refs if re.search(r"_zz9999", b.lower())]
    check("images-exist", not missing, "every referenced image exists",
          f"{len(missing)} referenced files not in images/, e.g. {missing[:3]}")
    check("no-non-images", not nonimg, "no .pdf/.tif referenced",
          f"non-image files referenced: {nonimg[:3]}")
    check("no-orphan-images", not orphan, "no orphan-product images referenced",
          f"orphan images referenced: {orphan[:3]}")

    # 4. main_image <= 1 per row (find the main col by name)
    main_cols = [c for c in header if c.strip().lower() in ("main_image", "main image", "main")]
    over = []
    if main_cols:
        for r, v in cand.items():
            n = sum(len(v.get(c, [])) for c in main_cols)
            if n > 1: over.append(r)
    check("main-image-single", not over, "main_image has <=1 per article",
          f"{len(over)} articles have >1 main_image, e.g. {over[:3]}", warn=not main_cols)

    # 5. hero_video (null prop) must not be emitted
    check("skip-null-property", not any("hero" in c.lower() and "video" in c.lower() for c in header),
          "hero_video not emitted", "hero_video column present (should be skipped)")

    # 6. landmine coverage: case-mismatch + whitespace articles resolved
    def has_any(prefix):
        return any(r.lower().startswith(prefix) and any(cand[r].values()) for r in cand)
    check("case-mismatch-resolved", has_any("od0001003"),
          "case-mismatch article (OD0001003) got images",
          "OD0001003 has no images — likely case-sensitive join", warn=True)

    # 7. coverage vs gold (basename set overlap, property-agnostic)
    def flat(d): return {(r.lower(), b) for r, v in d.items() for lst in v.values() for b in lst}
    g, cflat = flat(gold), flat(cand)
    inter = len(g & cflat)
    cov = inter * 100 // max(len(g), 1)
    print(f"  [i] coverage vs gold: {inter}/{len(g)} placements matched ({cov}%) | "
          f"extra not in gold: {len(cflat - g)}")

    print(f"\n== score: {score}/{total} checks passed | gold-coverage {cov}% ==")

if __name__ == "__main__":
    main()
