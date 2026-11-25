#!/usr/bin/env python3
"""
discover.py - find which job system (Greenhouse, Lever, Ashby) each company in
candidates.json uses, by trying likely board names against the public feeds.

Usage:
    python3 discover.py           # writes out/discovered.md
    python3 discover.py --add     # also appends confirmed hits to companies.json

Rules (to avoid false matches):
  - A hit only counts if the feed answers AND has at least one posting.
  - For Greenhouse, the board's own name must resemble the company name.
  - A miss is "not found under the names tried", never "doesn't exist".
"""
import argparse
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBES = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}
GH_META = "https://boards-api.greenhouse.io/v1/boards/{slug}"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "job-radar/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError, TimeoutError):
        return None


def squash(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def variants(c):
    base = c["name"].lower()
    words = re.findall(r"[a-z0-9]+", base)
    v = list(c.get("slugs", []))
    v += ["".join(words), "-".join(words)]
    trimmed = [w for w in words if w not in ("games", "studios", "studio", "inc", "media", "the")]
    if trimmed:
        v.append("".join(trimmed))
    seen, out = set(), []
    for s in v:
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def count_jobs(ats, data):
    if data is None:
        return 0
    if ats == "lever":
        return len(data) if isinstance(data, list) else 0
    return len(data.get("jobs", [])) if isinstance(data, dict) else 0


def name_ok(company, slug):
    meta = get(GH_META.format(slug=slug)) or {}
    board = squash(meta.get("name", ""))
    want = squash(company)
    return bool(board) and (board in want or want in board or board[:5] == want[:5])


def probe(c):
    for slug in variants(c):
        for ats, url in PROBES.items():
            n = count_jobs(ats, get(url.format(slug=slug)))
            if n == 0:
                continue
            if ats == "greenhouse" and not name_ok(c["name"], slug):
                continue
            return {"ats": ats, "slug": slug, "jobs": n}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--add", action="store_true", help="append hits to companies.json")
    args = ap.parse_args()

    cands = json.loads((HERE / "candidates.json").read_text())["candidates"]
    comp_path = HERE / "companies.json"
    comp = json.loads(comp_path.read_text())
    have = {squash(x["name"]) for x in comp["companies"]}

    hits, misses = [], []
    for c in cands:
        if squash(c["name"]) in have:
            continue
        r = probe(c)
        (hits if r else misses).append((c, r))
        print(("HIT  " if r else "miss ") + c["name"] + (f" -> {r['ats']}/{r['slug']} ({r['jobs']} jobs)" if r else ""))

    lines = ["# Feed discovery results", "", "## Found", "| Company | Region | System | Slug | Open jobs |", "|---|---|---|---|---|"]
    lines += [f"| {c['name']} | {c.get('region','')} | {r['ats']} | {r['slug']} | {r['jobs']} |" for c, r in hits]
    lines += ["", "## Not found under the names tried (check the careers page apply link by hand)"]
    lines += [f"- {c['name']} (tried: {', '.join(variants(c))})" for c, _ in misses]
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out" / "discovered.md").write_text("\n".join(lines) + "\n")

    if args.add and hits:
        for c, r in hits:
            tier = "3-small-midwest" if c.get("region") == "midwest" else "3-small-us"
            comp["companies"].append({"name": c["name"], "ats": r["ats"], "slug": r["slug"], "tier": tier})
        comp_path.write_text(json.dumps(comp, indent=2) + "\n")
    print(f"{len(hits)} found, {len(misses)} not found -> out/discovered.md")


if __name__ == "__main__":
    main()
