#!/usr/bin/env python3
"""Generate the ohso-dayone interview dataset: dummy products, text-on-image assets,
a loose mapping — with deliberate real-world landmines planted throughout.

Deterministic (fixed seed) so the dataset + its pitfalls are reproducible.
Run:  python3 generate.py
Out:  data/products.csv  data/mapping.json  data/images/*.png (+ a couple non-images)
"""
import csv, json, os, random, textwrap
from PIL import Image, ImageDraw, ImageFont


def _font(size):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc",
              "/Library/Fonts/Arial.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)      # Pillow >=10 scalable default
    except TypeError:
        return ImageFont.load_default()

random.seed(7)
HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "data", "images")
os.makedirs(IMG_DIR, exist_ok=True)

# ---- funny product vocabulary -------------------------------------------------
MODELS = [
    "Orphan Discobombulator", "Bender Straightener", "Quantum Noodle Rehydrator",
    "Existential Toaster", "Reverse Yeti Whisperer", "Turbo Sock Untangler",
    "Passive Aggressive Kettle", "Nocturnal Lawn Persuader", "Emotional Support Anvil",
    "Baroque Spoon Amplifier", "Feral Calculator", "Wandering Umbrella Magnet",
    "Sentient Doormat", "Overqualified Paperweight", "Melancholy Disco Ball",
    "Aggressive Cushion", "Recursive Ladder", "Invisible Highlighter",
    "Procrastination Timer", "Interpretive Wrench", "Haunted Fondue Set",
    "Ambivalent Snorkel", "Suspicious Beanbag", "Elastic Doorknob",
    "Nostalgic Flashlight", "Diplomatic Chainsaw", "Vegan Crowbar",
    "Introverted Megaphone", "Gluten-Free Hammer", "Ergonomic Boomerang",
]
COLORS = ["Blazing Beige", "Existential Teal", "Panic Pink", "Voidwash Black",
          "Suspicious Orange", "Mild Mauve", "Radioactive Sage", "Beige²", "Ümlaut Grün"]
SIZES = ["XS", "S", "M", "L", "XL", "42", "44", "OneSize"]
TAXONOMIES = ["100100", "100200", "200100", "300100"]   # a few "categories"
SEASONS = ["202500", "202600"]

# slot vocab (view_pic). picture types: GHO ghost, MOD model, PLP card, BEA beauty
VIEWS = ["0", "1", "2", "3", "D1", "D2"]
PICS = ["GHO", "MOD", "PLP", "BEA"]

BG = {"GHO": (238, 238, 240), "MOD": (215, 230, 245), "PLP": (245, 235, 210),
      "BEA": (235, 220, 235), "PDF": (250, 220, 220), "TIF": (220, 250, 220)}


F_TITLE, F_BODY, F_SLOT = _font(46), _font(30), _font(64)


def make_image(path, name, base, view, pic, bg):
    W = H = 800
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    d.rectangle([10, 10, W - 11, H - 11], outline=(90, 90, 90), width=4)
    # header bar with the pic type
    d.rectangle([10, 10, W - 11, 90], fill=(60, 60, 70))
    d.text((34, 30), f"{pic}", font=_font(44), fill=(255, 255, 255))
    # centered big slot label (the key info: view_pic)
    slot = f"{view}_{pic}"
    tw = d.textlength(slot, font=F_SLOT)
    d.text(((W - tw) / 2, 150), slot, font=F_SLOT, fill=(25, 25, 30))
    # article name (wrapped) + id
    y = 300
    for wrapped in textwrap.wrap(name, 26)[:3]:
        d.text((40, y), wrapped, font=F_TITLE, fill=(20, 20, 20)); y += 60
    y += 20
    d.text((40, y), f"ID  {base}", font=F_BODY, fill=(70, 70, 70)); y += 44
    d.text((40, y), f"view {view}   pic {pic}", font=F_BODY, fill=(70, 70, 70))
    im.save(path)


def code(prefix, n):
    return f"{prefix}{n:07d}"


def main():
    prod_rows = []
    # header mirrors a trimmed product-catalogue export
    header = ["RECORD_ID", "RECORD_NAME", "ARTICLE_NAME", "PRODUCT_CODE",
              "TAXONOMY", "COLOR", "SIZE", "parent_id", "level"]

    images = []          # (filename, name, base, view, pic, bg)
    articles_meta = []   # for pitfalls / interviewer notes
    art_counter = 1000
    corrupt = {"case_mismatch": [], "whitespace": [], "zeropad": [], "orphan": [],
               "no_images": [], "dup_slot": [], "unicode": [], "comma": [],
               "dup_row_case": [], "missing_hero": []}

    for mi, model_name in enumerate(MODELS):
        prefix = "".join([w[0] for w in model_name.split()][:2]).upper()
        prefix = (prefix + "X")[:2]
        model_code = f"{prefix}{mi:04d}$"
        tax = random.choice(TAXONOMIES)
        season = random.choice(SEASONS)
        # master model row
        mrec = f"{model_code}_{season}".replace("$_", "$_")
        prod_rows.append([model_code, model_name, "", model_code, tax, "", "",
                          "", "master_model"])
        # season node
        srec = f"{model_code}_{season}"
        prod_rows.append([srec, model_name, "", model_code, tax, "", "",
                          model_code, "season"])

        n_articles = random.randint(5, 9)
        for _ in range(n_articles):
            art_counter += 1
            color = random.choice(COLORS)
            acode = code(prefix, art_counter) + "+"
            arec = f"{acode}_{season}"
            aname = f"{model_name} {color}"
            # planted: embedded comma in one name
            if art_counter == 1007:
                aname = f"{model_name}, Special, Edition {color}"; corrupt["comma"].append(acode)
            # planted: unicode already possible via Ümlaut/Grün/Beige² colors
            if any(ch in aname for ch in "Üößé²"):
                corrupt["unicode"].append(acode)
            prod_rows.append([arec, aname, aname, acode, tax, color, "",
                              srec, "article"])
            # SKUs
            for size in random.sample(SIZES, random.randint(1, 4)):
                scode = code(prefix, art_counter) + size
                prod_rows.append([f"{scode}_{season}", aname, aname, scode, tax,
                                  color, size, arec, "sku"])

            base = acode.rstrip("+")
            # decide image set for this article
            roll = random.random()
            if roll < 0.08:                       # ~8% get NO images
                corrupt["no_images"].append(acode); continue

            # normal: a spread of GHO views + a MOD + sometimes PLP
            slots = []
            has_hero = random.random() > 0.18      # ~18% missing the 0_GHO hero
            if has_hero:
                slots.append(("0", "GHO"))
            else:
                slots.append(("3", "GHO")); corrupt["missing_hero"].append(acode)
            slots += [("1", "GHO"), ("2", "GHO"), ("0", "MOD")]
            if random.random() > 0.5:
                slots.append(("D1", "GHO"))
            if random.random() > 0.7:
                slots.append(("0", "PLP"))
            if random.random() > 0.85:            # BEA occasionally
                slots.append(("0", "BEA"))

            for vi, (view, pic) in enumerate(slots):
                fcode = base
                fview = view
                # planted corruptions on filenames
                if art_counter == 1003 and vi == 0:
                    fcode = base.lower(); corrupt["case_mismatch"].append(acode)   # case mismatch
                if art_counter == 1005 and view == "1":
                    fview = "01"; corrupt["zeropad"].append(acode)                 # zero-pad view
                fn = f"DSC_{fcode}_{fview}_{pic}_{aname.split()[0]}.png"
                images.append((fn, aname, base, view, pic, BG[pic]))
                # planted: duplicate slot (same code/view/pic, different file) for one article
                if art_counter == 1009 and vi == 0:
                    images.append((f"DSC_{base}_{view}_{pic}_{aname.split()[0]}-alt.png",
                                   aname, base, view, pic, BG[pic]))
                    corrupt["dup_slot"].append(acode)

    # planted: duplicate product row differing only by case
    dupe = list(prod_rows[3]); dupe[0] = dupe[0].lower(); dupe[3] = dupe[3].lower()
    prod_rows.append(dupe); corrupt["dup_row_case"].append(dupe[0])
    # planted: trailing whitespace in a couple codes
    prod_rows[5][3] = prod_rows[5][3] + "  "; corrupt["whitespace"].append(prod_rows[5][0])

    # planted: orphan images (codes with no product)
    for oc in ["ZZ9999001", "ZZ9999002", "zz9999003"]:
        images.append((f"DSC_{oc}_0_GHO_Ghostproduct.png",
                       f"Ghost Product {oc}", oc, "0", "GHO", BG["GHO"]))
        corrupt["orphan"].append(oc)

    # planted: non-image files mixed into the images pile
    images_meta_noninage = []
    with open(os.path.join(IMG_DIR, "DSC_OD1002_0_DOC_manual.pdf"), "w") as f:
        f.write("%PDF-1.4 fake certificate not an image\n")
    # a fake .tif (just a renamed png-ish blob)
    make_image(os.path.join(IMG_DIR, "DSC_OD1002_0_GHO_bigfile.tif"),
               "I claim to be a TIFF", "OD1002", "0", "GHO", BG["TIF"])

    # write products.csv
    with open(os.path.join(HERE, "data", "products.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(prod_rows)

    # render images
    for fn, name, base, view, pic, bg in images:
        make_image(os.path.join(IMG_DIR, fn), name, base, view, pic, bg)

    # mapping.json — simplified 3 properties, with a planted typo + a null property
    def order(*slots):
        return {"order": list(slots)}
    mapping = {
        "main_image": {t: {"order": ["0_GHO"], "fallbacks": {"0_GHO": ["3_GHO", "0_MOD"]}}
                       for t in TAXONOMIES} | {"default": {"order": ["0_GHO"], "fallbacks": {"0_GHO": ["3_GHO"]}}},
        "gallery": {t: order("0_GHO", "1_GHO", "2_GHO", "D1_GHO", "0_MOD") for t in TAXONOMIES}
                   | {"default": order("0_GHO", "1_GHO", "2_GHO")},
        "plp_cards": {t: order("0_PLP") for t in TAXONOMIES},
        "hero_video": None,                      # planted: null property (must be skipped)
    }
    # planted mapping typo: a split token in one taxonomy's gallery
    mapping["gallery"]["200100"] = {"order": ["0_GHO", "1_GHO", "D1", "BEA", "2_GHO"]}
    with open(os.path.join(HERE, "data", "mapping.json"), "w") as f:
        json.dump(mapping, f, indent=1, ensure_ascii=False)

    # summary + interviewer key
    n_img = len([f for f in os.listdir(IMG_DIR) if f.lower().endswith(".png")])
    print("products rows :", len(prod_rows))
    print("image files   :", len(os.listdir(IMG_DIR)), f"({n_img} png)")
    print("planted pitfalls:")
    for k, v in corrupt.items():
        print(f"   {k:14} {len(v)}  {v[:3]}")
    json.dump({k: v for k, v in corrupt.items()},
              open(os.path.join(HERE, "_planted_pitfalls.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
