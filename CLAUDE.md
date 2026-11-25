# Job Radar workspace - instructions for Claude

This repo finds jobs early and turns the best ones into applications.

## The daily loop
1. GitHub Actions runs `job_radar.py` every morning and opens a "N new jobs" issue when there are new matches.
2. **radar-ranker** scores that digest against `profile/profile.md` and picks the top 2-3.
3. For each pick: **ats-detective** (which applicant system it uses and what that means for the resume) -> **ruthless-cv-optimizer** (tailor from the base resume) -> **cover-letter-writer**.
4. Outreach to a real person at the company within 48 hours of applying.
5. **star-story-extractor** and **evidence-miner** keep `story-bank/` growing; **mock-interviewer** rehearses once an interview lands; **linkedin-360brew-planner** drafts posts.

## Rules that override any skill
- **No fabrication.** Only facts from `profile/profile.md`, `story-bank/`, or what the user says. Ask, don't estimate. Concurrent roles never add calendar years.
- **Never name internal tools, product names, architecture documents or vendors** from current or past employers in anything that leaves this repo. Describe the engineering problem and the reasoning instead.
- **Resumes are LaTeX, one page per variant**, all built from the base resume. When a skill would write a Markdown CV, edit a copy of the `.tex` instead if one exists in `resume/`, and still produce the skill's scorecard.
- **Seniority:** follow the profile's Ranking inputs.
- **Lead with a question when a decision is the user's to make.** Decide one step at a time, with the reasoning shown first.

## Files
- `companies.json`, `candidates.json`, `filters.json`: what the radar watches (see README)
- `profile/profile.md`: verified experience inventory, read by every skill (git-ignored: this repo is public)
- `resume/base.tex`: the base resume every tailored version starts from (git-ignored)
- `story-bank/`: STAR stories, one per file
- `output/`: tailored resumes, cover letters, interview debriefs
- `.claude/skills/`: radar-ranker (custom) plus seven skills adapted from open-career-skills (see THIRD_PARTY_LICENSES.md)
