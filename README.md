# granola-export

Scripts for exporting and converting [Granola](https://www.granola.ai) meeting transcripts.

Requires a Granola account on the **Business or Enterprise** plan.

---

## Scripts

### `granola.py` — Export + convert in one step

Fetches all your meeting notes from the Granola API and writes them as Markdown files. JSON responses are cached locally so re-runs only fetch new or changed notes.

```bash
GRANOLA_API_KEY=grn_... python granola.py --output-dir ./transcripts
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | `.` | Directory to write Markdown files. A `.cache/` subdirectory is created here for raw JSON. |
| `--overwrite` | off | Re-fetch and re-render all notes, ignoring the cache. |

---

### `export_transcripts.py` + `json_to_markdown.py` — Two-step pipeline

If you prefer to keep the raw JSON and Markdown conversion as separate steps:

**Step 1: Export JSON**
```bash
GRANOLA_API_KEY=grn_... python export_transcripts.py --output-dir ./granola_export
```

**Step 2: Convert to Markdown**
```bash
python json_to_markdown.py --input-dir ./granola_export --output-dir ./granola_markdown
```

| Flag | Default | Description |
|------|---------|-------------|
| `export_transcripts.py --output-dir` | `./granola_export` | Where to save JSON files. |
| `export_transcripts.py --no-skip-existing` | off | Re-download and overwrite existing files. |
| `json_to_markdown.py --input-dir` | `./granola_export` | Where to read JSON files from. |
| `json_to_markdown.py --output-dir` | `./granola_markdown` | Where to write Markdown files. |
| `json_to_markdown.py --overwrite` | off | Overwrite existing Markdown files. |

---

## Output format

Each note is saved as a Markdown file with YAML front matter:

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

- `project` is derived from the note's folder name in Granola, slugified to kebab-case.
- `**You**` is audio captured from your microphone; `**Them**` is system audio (other participants).
- Consecutive segments from the same speaker are merged into single utterances.

---

## Setup

```bash
pip install requests
```

Get your API key from Granola → Settings → API → Create new key. The key should be set as an environment variable:

```bash
export GRANOLA_API_KEY=grn_...
```

---

## Rate limits

The Granola API allows 25 requests per 5 seconds (burst) and 5 requests per second (sustained). The scripts add a 250ms delay between requests to stay within limits. If you hit a 429, the script waits 10 seconds before retrying.

Some notes may return a 502 error — this is a server-side issue with that specific note and is not recoverable from the client side.
