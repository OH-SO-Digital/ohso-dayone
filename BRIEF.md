# Day-One Assignment — Product Image Syndication

## Background — the world you're working in

We sell delightful nonsense (Orphan Discobombulators, Emotional Support Anvils, and the like).
Three systems are involved:

- **System A — Product catalogue (PIM).** The source of truth for *products*: models, their
  articles (colour variants), size variants, and each product's category (taxonomy). You've been
  given an export from it: **`data/products.csv`**.
- **System B — Digital Asset Management (DAM).** Where all the *imagery* lives. You've been given
  a dump of its files: **`data/images/`**.
- **System C — the destination (a storefront / commerce platform).** It shows products online and
  needs each product wired up to the right images, in the right places. It consumes an **import
  file** that you produce.

```
  System A (PIM)          System B (DAM)
  products.csv            images/
        \                   /
         \                 /
          >-- YOUR JOB ---<        guided by  data/mapping.json
                 |
                 v
        import file  ──►  System C (storefront)
```

The **mapping** (`data/mapping.json`) is the business rule that says *which* images fill *which*
image slots on a product (e.g. a main image, a gallery, product-listing cards).

## What you have

In `data/`:
- **`products.csv`** — products from System A.
- **`images/`** — image files from System B (the DAM).
- **`mapping.json`** — the slot rules.

## What we want

Produce the **import file for System C** that attaches the right images to the right products, in
the right order, according to the mapping. Something we could actually feed into System C.

That's it. Ship what you'd be comfortable importing.

## Notes

- Work however you like; any language/tools.
- Timebox: ~90 minutes. We care more about how you reason than about a perfect result.
- The three systems don't agree on everything — the data is real-world messy. If something looks
  off, use your judgement, and **tell us what you decided and why**.
- If anything about the goal or the data is unclear, **ask** — that's expected, not penalised.

Good luck.
