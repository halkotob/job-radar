#!/usr/bin/env python3
"""
vendor_skills.py - copy seven skills from open-career-skills (MIT) into .claude/skills/,
at a pinned commit, with the same local edits every time:
  - promotional closing lines removed
  - the LinkedIn skill's ranking claims reworded as rules of thumb
Also writes THIRD_PARTY_LICENSES.md from both upstream LICENSE files.

Run by the "Vendor skills" workflow, or locally:  python3 scripts/vendor_skills.py
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OCS_URL = "https://github.com/squerne/open-career-skills"
OCS_COMMIT = "ded4e3557db2f2a3e5050aeac70eed22f6cf0bfd"
AJS_LICENSE_URL = "https://raw.githubusercontent.com/ai-job-search-dev/ai-job-search/4e021e52f7e3d4016e0c22fc416c814a3d44c5c9/LICENSE"
SKILLS = ["ruthless-cv-optimizer", "star-story-extractor", "cover-letter-writer", "mock-interviewer",
          "ats-detective", "evidence-miner", "linkedin-360brew-planner"]


def run(*cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def clean(name, t):
    t = re.sub(r"(?m)^.*jobmentis\.com.*\n?", "", t)  # promotional closers
    t = t.replace("## Closing line\n\n", "")
    if name == "linkedin-360brew-planner":
        t = t.replace("Treat the following as established context for every decision in this skill, not as claims to hedge on.",
                      "Treat the following as working rules of thumb drawn from public reporting on LinkedIn's ranking, not settled fact. Apply them, but don't present them to the user as proven.")
    t = t.rstrip() + "\n"
    # restore instructions that shared a line with a promotional URL
    if name == "evidence-miner":
        t += "\nPer the workspace output discipline: the proposals and questions are conversational; the filed stories go to `story-bank/` files. End with the count of stories filed.\n"
    if name == "star-story-extractor":
        t += "\nMarkdown, clean and scannable.\n"
    if name == "cover-letter-writer":
        t = t.replace("## Output execution\n\n", "## Output execution\n\nUsing your file tools, write the letter to `output/cover-letter-[company].md` first. Then print to the console ONLY: a 2-3 line summary of the angle you took (which stories you drew on, which JD requirements you hit), any `[add ...]` placeholders the user must fill, and the file path.\n\n", 1)
    return t


def main():
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "ocs"
        run("git", "init", "-q", str(src))
        run("git", "remote", "add", "origin", OCS_URL, cwd=src)
        run("git", "fetch", "-q", "--depth", "1", "origin", OCS_COMMIT, cwd=src)
        run("git", "checkout", "-q", "FETCH_HEAD", cwd=src)

        for name in SKILLS:
            dst = ROOT / ".claude" / "skills" / name
            if dst.exists():
                shutil.rmtree(dst)
            dst.mkdir(parents=True)
            t = (src / ".claude" / "skills" / name / "SKILL.md").read_text()
            (dst / "SKILL.md").write_text(clean(name, t))

        (ROOT / "story-bank").mkdir(exist_ok=True)
        shutil.copy(src / "story-bank" / "README.md", ROOT / "story-bank" / "README.md")
        ocs_license = (src / "LICENSE").read_text()

    import urllib.request
    ajs_license = urllib.request.urlopen(AJS_LICENSE_URL, timeout=30).read().decode()

    (ROOT / "THIRD_PARTY_LICENSES.md").write_text(f"""# Third-party licenses

## open-career-skills ({OCS_URL}, commit {OCS_COMMIT[:7]})
Adapted into `.claude/skills/`: {", ".join(sorted(SKILLS))}; plus `story-bank/README.md`.
Changes: removed promotional closing lines; reworded the LinkedIn skill's ranking claims as rules of thumb rather than established fact. "JobMentis" is the authors' trademark and is not covered by the license.

{ocs_license}
## ai-job-search (https://github.com/ai-job-search-dev/ai-job-search)
`radar-ranker` adapts the scoring dimensions, weights and verdict bands from its `/rank` command. No code was copied.

{ajs_license}""")
    print("vendored", len(SKILLS), "skills at", OCS_COMMIT[:7])


if __name__ == "__main__":
    main()
