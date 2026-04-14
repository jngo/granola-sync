# granola-export

Export [Granola](https://www.granola.ai) meeting transcripts as Markdown files, with YAML front matter suitable for use in an Obsidian vault or with AI agents.

Requires a Granola account on the **Business or Enterprise** plan.

---

## Setup

```bash
# 1. Clone the repo and symlink the skill
git clone https://github.com/jngo/granola-export.git
ln -s "$(pwd)/granola-export/skills/granola-sync" ~/.claude/skills/granola-sync

# 2. Add your API key
cp granola-export/.env.example granola-export/.env
# Edit .env and set GRANOLA_API_KEY

# 3. Install dependencies and register the CLI
python3 ~/.claude/skills/granola-sync/scripts/granola.py --setup
```

This installs `requests` into a dedicated venv and symlinks `granola-sync` to `~/.local/bin/`. Make sure `~/.local/bin` is in your `PATH`.

## Usage

### CLI

```bash
GRANOLA_API_KEY=grn_... granola-sync --output-dir ./transcripts
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | `.` | Directory to write Markdown files. A `.cache/` subdirectory stores raw JSON, keyed by note ID. |
| `--overwrite` | off | Re-fetch and re-render all notes, ignoring the cache. |

Re-runs skip already-cached notes, so only new transcripts are fetched.

### Claude Code skill

With the symlink in place, run `/granola-sync` in Claude Code and follow the prompts. Because it's a symlink, updates pulled from this repo are immediately reflected in the skill — no reinstall needed.

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
