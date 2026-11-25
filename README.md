# Job Radar

Checks the public job feeds of your target companies every morning and lists only the matching roles you haven't seen yet. Runs free on GitHub Actions.

## Set up (once)
1. On GitHub, go to **Actions** and enable workflows if GitHub asks.
2. Run **Vendor skills** once. It copies the career skills in from open-career-skills (MIT) at a pinned commit.
3. Run **Discover feeds**. It probes `candidates.json` and adds every confirmed company to `companies.json`.
4. Run **Daily job radar** for the first run. It lists every current match. After that it runs at about 7:17am Detroit time and lists only new postings.

**This repo is public.** Your resume, profile, story bank and generated outputs are git-ignored, so they live only on your machine (and in the career coaching project). To use the skills locally, clone the repo and put `profile/profile.md` and `resume/base.tex` back in.

## Daily loop
1. The radar opens a "N new jobs" issue each morning when there are new matches.
2. A daily Claude task reads that issue, ranks the jobs with `radar-ranker`, and saves the shortlist to the career coaching project.
3. Pick from the shortlist, then tailor the resume, write the cover letter, apply, and contact a real person there within 48 hours.

## Skills (open the folder in Claude Code and they load automatically)
| Skill | When to use it |
|---|---|
| `radar-ranker` | Paste a "N new jobs" issue and it ranks fit, says what's missing, and picks the top 2-3 |
| `ats-detective` | Which applicant system a company uses, and the resume rules that follow |
| `ruthless-cv-optimizer` | Tailor your base resume to one job. Asks before it rewrites, never invents numbers |
| `cover-letter-writer` | 300-400 word letter built from your real stories |
| `star-story-extractor` | Braindump a win and it files a STAR story in `story-bank/`, or matches stories to a job description |
| `evidence-miner` | Mines your git history for achievements you forgot |
| `mock-interviewer` | One question at a time, then an honest debrief |
| `linkedin-360brew-planner` | LinkedIn post ideas and drafts from your real stories |

`profile/profile.md` is your verified experience, and every skill reads it. Fix the lines marked `> confirm`. Credits and licenses are in `THIRD_PARTY_LICENSES.md`.

## Files
| File | What it does |
|---|---|
| `job_radar.py` | Pulls the feeds, filters the titles, keeps only unseen jobs, writes `out/new_jobs_DATE.md` |
| `discover.py` | Works out which system a company uses (Greenhouse, Lever or Ashby) |
| `companies.json` | Companies checked daily |
| `candidates.json` | Companies to probe next. Add names here, then run Discover feeds |
| `filters.json` | Title words to keep and drop. Matching is whole-word, so "SRE" won't match "measure" |
| `seen.json` | Jobs already reported. Delete it to start fresh |

## Run locally (optional)
`python3 job_radar.py --descriptions` (Python 3.8+, nothing to install)

Companies on Workday or their own careers sites (Blizzard, EA, Netflix, Disney, Adobe, Amazon, WBD and others) have no simple feed like this, so check those by hand.
