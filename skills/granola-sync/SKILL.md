---
name: granola-sync
description: Exports Granola meeting transcripts as Markdown to a local directory. Use when the user wants to export, sync, or update their Granola meeting transcripts.
compatibility: Requires Python 3.x (standard library only, no dependencies).
allowed-tools: Bash
metadata:
  author: jngo
  version: "1.3"
---

# Granola Sync

Syncs Granola meeting transcripts as Markdown files to a specified output directory. JSON responses are cached in `~/.cache/granola/` keyed by note ID — cached notes are skipped on subsequent runs unless `--overwrite` is passed.

## Credentials

The API key is stored in `~/.claude/skills/granola-sync/.env`. If this file does not exist, create it:

```bash
echo 'GRANOLA_API_KEY=grn_...' > ~/.claude/skills/granola-sync/.env
```

Then open the file and set `GRANOLA_API_KEY` to a valid key (generated at Granola → Settings → API → Create new key).

## Running the sync

Load the `.env` file and run:

```bash
set -a && source ~/.claude/skills/granola-sync/.env && set +a
granola-sync --output-dir <output-dir>
```

## Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `--output-dir` | No | `.` (current directory) | Where to write Markdown files |
| `--overwrite` | No | Off | Re-fetch and re-render all notes, ignoring the cache |

## Steps

1. Check that `~/.claude/skills/granola-sync/.env` exists and `GRANOLA_API_KEY` is set. If not, prompt the user to create the file and fill in their key before proceeding.
2. Ask the user for the output directory, or use the current directory if not specified.
3. Run the sync, streaming output to the user so they can see progress:
   ```bash
   set -a && source ~/.claude/skills/granola-sync/.env && set +a && granola-sync --output-dir <output-dir>
   ```
4. On completion, report the number of transcripts exported and any failures.
