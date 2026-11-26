#!/usr/bin/env python3
"""
job_radar.py - pull public job feeds (Greenhouse, Lever, Ashby) for a list of
target companies, keep only roles that match your search terms, and write out
the ones you haven't seen before.

Usage:
    python3 job_radar.py                  # normal daily run
    python3 job_radar.py --descriptions   # include trimmed job descriptions (for fit ranking)
    python3 job_radar.py --dry-run        # show what's new without marking it seen

Files:
    companies.json   which companies to check (edit this to add more)
    filters.json     which titles to keep / drop (edit this to tune)
    seen.json        every job ID already reported (created automatically)
    out/new_jobs_YYYY-MM-DD.md   today's digest, ready to paste into Claude

Standard library only - no pip installs needed.
"""
import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FEEDS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}
DESC_CHARS = 1500  # how much of each description to keep in the digest


# ---------- fetching ----------

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "job-radar/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def strip_html(text):
    text = html.unescape(text or "")          # Greenhouse double-escapes its HTML
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


# ---------- normalizing: every ATS -> one shape ----------

def normalize(ats, company, data):
    """Return a list of dicts: id, company, title, location, url, posted, description."""
    jobs = []
    if ats == "greenhouse":
        for j in data.get("jobs", []):
            jobs.append({
                "id": str(j["id"]),
                "title": j.get("title", ""),
                "location": (j.get("location") or {}).get("name", ""),
                "url": j.get("absolute_url", ""),
                "posted": (j.get("first_published") or j.get("updated_at") or "")[:10],
                "description": strip_html(j.get("content", "")),
            })
    elif ats == "lever":
        for j in data:
            created = j.get("createdAt")
            cats = j.get("categories") or {}
            jobs.append({
                "id": str(j["id"]),
                "title": j.get("text", ""),
                "location": cats.get("location", "") or ", ".join(cats.get("allLocations", []) or []),
                "url": j.get("hostedUrl", ""),
                "posted": dt.datetime.fromtimestamp(created / 1000, dt.timezone.utc).strftime("%Y-%m-%d") if created else "",
                "description": (j.get("descriptionPlain") or strip_html(j.get("description", ""))).strip(),
            })
    elif ats == "ashby":
        for j in data.get("jobs", []):
            if j.get("isListed") is False:
                continue
            jobs.append({
                "id": str(j["id"]),
                "title": j.get("title", ""),
                "location": j.get("location", "") + (" (remote ok)" if j.get("isRemote") else ""),
                "url": j.get("jobUrl", ""),
                "posted": (j.get("publishedAt") or "")[:10],
                "description": (j.get("descriptionPlain") or strip_html(j.get("descriptionHtml", ""))).strip(),
            })
    else:
        raise ValueError(f"unknown ats: {ats}")
    for j in jobs:
        j["company"] = company
        j["key"] = f"{ats}:{company}:{j['id']}"
    return jobs


# ---------- filtering ----------

def word_match(term, text):
    # whole-word, case-insensitive; "SRE" must not match "measure"
    return re.search(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])", text) is not None


def keep(job, filters):
    title = job["title"].lower()
    if any(word_match(t, title) for t in filters["exclude_title"]):
        return False
    return any(word_match(t, title) for t in filters["include_title"])


# ---------- main ----------

def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--descriptions", action="store_true", help="include trimmed descriptions")
    ap.add_argument("--dry-run", action="store_true", help="don't update seen.json")
    args = ap.parse_args()

    companies = load(HERE / "companies.json", {})["companies"]
    filters = load(HERE / "filters.json", {})
    seen_path = HERE / "seen.json"
    seen = set(load(seen_path, []))

    new, errors, checked = [], [], 0
    for c in companies:
        url = FEEDS[c["ats"]].format(slug=c["slug"])
        try:
            jobs = normalize(c["ats"], c["name"], fetch_json(url))
        except Exception as e:  # one bad feed shouldn't stop the run
            errors.append(f"{c['name']} ({c['ats']}/{c['slug']}): {e}")
            continue
        checked += len(jobs)
        for j in jobs:
            if j["key"] not in seen and keep(j, filters):
                j["tier"] = c.get("tier", "")
                new.append(j)

    today = dt.date.today().isoformat()
    out_dir = HERE / "out"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"new_jobs_{today}.md"

    lines = [f"# New matching jobs - {today}",
             f"{len(new)} new matches from {checked} postings across {len(companies)} companies.", ""]
    for j in sorted(new, key=lambda x: (x["tier"], x["company"], x["title"])):
        lines.append(f"## {j['title']} - {j['company']}")
        lines.append(f"- Location: {j['location'] or 'n/a'}")
        lines.append(f"- Posted: {j['posted'] or 'n/a'}  |  Tier: {j['tier']}")
        lines.append(f"- Apply: {j['url']}")
        if args.descriptions and j["description"]:
            d = j["description"]
            lines.append(f"- Description: {d[:DESC_CHARS]}{'...' if len(d) > DESC_CHARS else ''}")
        lines.append("")
    if errors:
        lines += ["## Feeds that failed (check the slug)"] + [f"- {e}" for e in errors] + [""]
    if out_file.exists():
        # A second run on the same day (backup schedule or manual rerun) must never
        # wipe out the earlier digest. Add only what's new, under its own heading.
        if new or errors:
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%H:%M UTC")
            extra = [f"# Later run ({stamp}) - {len(new)} more new matches", ""] + lines[3:]
            with open(out_file, "a") as f:
                f.write("\n" + "\n".join(extra))
    else:
        out_file.write_text("\n".join(lines))

    if not args.dry_run:
        seen.update(j["key"] for j in new)
        seen_path.write_text(json.dumps(sorted(seen), indent=0))

    print(f"{len(new)} new matches -> {out_file}")
    gh_out = __import__("os").environ.get("GITHUB_OUTPUT")
    if gh_out:  # lets the GitHub Actions workflow decide whether to open an issue
        with open(gh_out, "a") as f:
            f.write(f"new_count={len(new)}\nout_file={out_file.relative_to(HERE)}\n")
    for e in errors:
        print("FEED ERROR:", e, file=sys.stderr)


if __name__ == "__main__":
    main()
