# granola-sync

Export [Granola](https://www.granola.ai) meeting transcripts as Markdown files, with YAML front matter suitable for use in an Obsidian vault or with AI agents.

Requires a Granola account on the **Business or Enterprise** plan.

---

## Install

Requires Python 3 and Git (standard library only — no other dependencies).

```bash
curl -fsSL https://raw.githubusercontent.com/jngo/granola-sync/main/install.sh | bash
```

This clones the repo to `~/.local/share/granola-sync`, symlinks `granola-sync` to `~/.local/bin/`, installs the Claude Code skill, and prompts for your API key. Make sure `~/.local/bin` is in your `PATH`.

Alternatively, install the skill directly via the [skills CLI](https://agentskills.io):

```bash
npx skills add jngo/granola-sync
```

Then run `python3 ~/.agents/skills/granola-sync/granola.py --setup` to wire up the CLI and save your API key.

### API key

Get your key from Granola → Settings → API → Create new key. The install prompts for it automatically and saves it to `.env` in the skill directory.

### Updates

Re-run the install command to pull the latest version:

```bash
curl -fsSL https://raw.githubusercontent.com/jngo/granola-sync/main/install.sh | bash
```

---

## Usage

### CLI

```bash
granola-sync --output-dir ./transcripts
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | `.` | Directory to write Markdown files. A `.cache/` subdirectory stores raw JSON, keyed by note ID. |
| `--overwrite` | off | Re-fetch and re-render all notes, ignoring the cache. |

Re-runs skip already-cached notes, so only new transcripts are fetched.

### Claude Code skill

Run `/granola-sync` in Claude Code and follow the prompts. Because the skill is symlinked back to the install directory, updates are reflected immediately after pulling.

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

## Rate limits

25 requests per 5 seconds (burst), 5 per second (sustained). The script adds a 250ms delay between requests. On a 429, it waits 10 seconds before retrying.

Some notes may return a 502 — this is a server-side issue with the specific note and is not recoverable from the client.
