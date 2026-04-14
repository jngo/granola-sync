---
name: granola-sync
description: Exports Granola meeting transcripts as Markdown to a local directory. Use when the user wants to export, sync, or update their Granola meeting transcripts.
compatibility: Requires Python 3.x and the requests library (installed automatically via venv).
allowed-tools: Bash
metadata:
  author: jngo
  version: "1.2"
---

# Granola Sync

Syncs Granola meeting transcripts as Markdown files to a specified output directory. JSON responses are cached in `~/.cache/granola/` keyed by note ID — cached notes are skipped on subsequent runs unless `--overwrite` is passed.

## Credentials

The API key is stored in `~/.claude/skills/granola-sync/.env`. If this file does not exist, copy the example and fill in the key:

```bash
cp ~/.claude/skills/granola-sync/.env.example ~/.claude/skills/granola-sync/.env
```

Then open `.env` and set `GRANOLA_API_KEY` to a valid key (generated at Granola → Settings → API → Create new key).

## Setup

On first run, install dependencies and register the CLI:

```bash
python3 ~/.claude/skills/granola-sync/scripts/granola.py --setup
```

This creates a venv at `~/.local/share/granola-sync/venv`, installs `requests`, and symlinks `granola-sync` to `~/.local/bin/`. Make sure `~/.local/bin` is in your `PATH`.

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

1. Check that `~/.claude/skills/granola-sync/.env` exists and `GRANOLA_API_KEY` is set. If not, prompt the user to copy `.env.example` and fill in their key before proceeding.
2. Ask the user for the output directory, or use the current directory if not specified.
3. Check whether the venv exists at `~/.claude/skills/granola-sync/scripts/.venv`. If not, create it and install `requests`.
4. Run the script in the background, streaming output to the user so they can see progress.
5. On completion, report the number of transcripts exported and any failures.
