# granola-export

Export [Granola](https://www.granola.ai) meeting transcripts as Markdown files, with YAML front matter suitable for use in an Obsidian vault or with AI agents.

Requires a Granola account on the **Business or Enterprise** plan.

---

## Usage

### Standalone script

```bash
GRANOLA_API_KEY=grn_... python granola.py --output-dir ./transcripts
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | `.` | Directory to write Markdown files. A `.cache/` subdirectory stores raw JSON, keyed by note ID. |
| `--overwrite` | off | Re-fetch and re-render all notes, ignoring the cache. |

Re-runs skip already-cached notes, so only new transcripts are fetched.

### Claude Code skill

`skills/granola-sync/SKILL.md` defines a [Claude Code](https://claude.ai/code) skill. Install it to use `/granola-sync` directly from Claude Code:

```bash
# 1. Symlink the skill into your Claude skills directory
ln -s "$(pwd)/skills/granola-sync" ~/.claude/skills/granola-sync

# 2. Add your API key
cp .env.example ~/.claude/skills/granola-sync/.env
# Edit .env and set GRANOLA_API_KEY

# 3. Set up the venv
python3 -m venv ~/.claude/skills/granola-sync/scripts/.venv
~/.claude/skills/granola-sync/scripts/.venv/bin/pip install requests -q
```

Then in Claude Code, run `/granola-sync` and follow the prompts. Because it's a symlink, any updates you pull from this repo are immediately reflected in the skill.

---

## Output format

Each note is written as:

```
YYYY-MM-DD <Title>.md
```

```markdown
---
type: transcript
created: 2025-06-03T07:05:14Z
status: closed
date: 2025-06-03T07:05:14Z
project: my-project
source: Granola
---

# Meeting Title

## Transcript

**You**: ...

**Them**: ...
```

- `project` is the note's Granola folder name, slugified to kebab-case.
- `**You**` is audio from your microphone; `**Them**` is system audio (other participants).
- Consecutive segments from the same speaker are merged into single utterances.
- Colons in titles are replaced: `Title: Subtitle` → `Title — Subtitle`, `1:1` → `1-1`.

---

## Setup

```bash
pip install requests
```

Get your API key from Granola → Settings → API → Create new key.

---

## Rate limits

25 requests per 5 seconds (burst), 5 per second (sustained). The script adds a 250ms delay between requests. On a 429, it waits 10 seconds before retrying.

Some notes may return a 502 — this is a server-side issue with the specific note and is not recoverable from the client.
