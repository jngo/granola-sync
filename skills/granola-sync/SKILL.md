---
name: granola-sync
description: Exports Granola meeting transcripts as Markdown to a local directory. Use when the user wants to export, sync, or update their Granola meeting transcripts.
compatibility: Requires Python 3.x (standard library only, no dependencies).
allowed-tools: Bash
metadata:
  author: jngo
  version: "2.0"
---

# Granola Sync

Syncs Granola meeting transcripts as Markdown files to a specified output directory. Notes are cached locally — re-runs only fetch what's new unless `--overwrite` is passed.

## Steps

1. Check that `granola-sync` is available on PATH:
   ```bash
   command -v granola-sync
   ```
   If not found, the CLI needs to be installed. Run `--setup` from wherever the skill was installed:
   - Via `npx skills add`: `python3 ~/.agents/skills/granola-sync/granola.py --setup`
   - Via `install.sh`: already handled — this shouldn't happen

2. Ask the user for the output directory, or use the current directory if not specified.

3. Run the sync:
   ```bash
   granola-sync --output-dir <output-dir>
   ```
   The script loads the API key automatically from `.env` in the skill directory. If the key is missing, it will prompt and save it before proceeding.

4. On completion, report the number of transcripts exported and any failures.

## Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `--output-dir` | No | `.` (current directory) | Where to write Markdown files |
| `--overwrite` | No | Off | Re-fetch and re-render all notes, ignoring the cache |
