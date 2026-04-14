#!/usr/bin/env python3
"""
Export Granola meeting transcripts as Markdown to a local directory.

Usage:
    granola-sync [--output-dir /path/to/vault/transcripts]
    granola-sync --setup

JSON responses are cached in <output-dir>/.cache/ keyed by note ID.
Delete a note's cache file to force a re-fetch and re-render.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# --- Setup ---

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent

SKILL_CLIENTS = {
    "claude": Path.home() / ".claude" / "skills",
    "cursor": Path.home() / ".cursor" / "skills",
}


def ensure_command():
    """Make the script executable and symlink it as granola-sync on PATH."""
    SCRIPT_PATH.chmod(SCRIPT_PATH.stat().st_mode | 0o111)

    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    link = bin_dir / "granola-sync"
    if not link.exists() or (link.is_symlink() and link.resolve() != SCRIPT_PATH):
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(SCRIPT_PATH)
        print(f"  Linked: granola-sync → {SCRIPT_PATH}")


def ensure_skill():
    """Symlink the skill into each detected client's skills directory."""
    skill_src = SCRIPT_DIR / "skills" / "granola-sync"
    for client, skills_dir in SKILL_CLIENTS.items():
        if not skills_dir.parent.exists():
            continue
        skills_dir.mkdir(parents=True, exist_ok=True)
        link = skills_dir / "granola-sync"
        if not link.exists() or (link.is_symlink() and link.resolve() != skill_src.resolve()):
            if link.exists() or link.is_symlink():
                link.unlink()
            link.symlink_to(skill_src)
            print(f"  Linked: {client} skill → {skill_src}")


def setup():
    """Symlink granola-sync to ~/.local/bin/ and install the skill."""
    print("Setting up granola-sync...")
    ensure_command()
    ensure_skill()
    print()
    print("Done. Make sure ~/.local/bin is in your PATH, then run:")
    print("  GRANOLA_API_KEY=grn_... granola-sync --output-dir ./transcripts")


# --- API ---

BASE_URL = "https://public-api.granola.ai"
REQUEST_DELAY = 0.25  # seconds between requests; burst: 25 req/5s, sustained: 5 req/s


def api_get(path: str, api_key: str, params: dict | None = None) -> dict:
    """Make a GET request to the Granola API and return parsed JSON."""
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise e


def list_all_notes(api_key: str) -> list[dict]:
    """Paginate through all notes and return a flat list of note summaries."""
    notes = []
    cursor = None
    page = 1

    while True:
        params = {"page_size": 30}
        if cursor:
            params["cursor"] = cursor

        data = api_get("/v1/notes", api_key, params)

        batch = data.get("notes", [])
        notes.extend(batch)
        print(f"  Page {page}: fetched {len(batch)} notes (total so far: {len(notes)})")

        if not data.get("hasMore") or not data.get("cursor"):
            break

        cursor = data["cursor"]
        page += 1
        time.sleep(REQUEST_DELAY)

    return notes


def get_note_with_transcript(api_key: str, note_id: str) -> dict:
    """Fetch a single note including its full transcript."""
    return api_get(f"/v1/notes/{note_id}", api_key, {"include": "transcript"})


# --- Markdown conversion ---

def iso_timestamp(raw: str) -> str:
    """Normalise an ISO datetime string to YYYY-MM-DDTHH:MM:SSZ, stripping milliseconds."""
    if not raw:
        return ""
    ts = raw[:19]
    if len(ts) == 19:
        return ts + "Z"
    return raw


def slugify(text: str) -> str:
    text = text.lower().replace(":", "-")
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text).strip("-")


def format_front_matter(note: dict) -> str:
    lines = ["---", "type: transcript"]

    created = iso_timestamp(note.get("created_at") or "")
    if created:
        lines.append(f"created: {created}")

    lines.append("status: closed")

    if created:
        lines.append(f"date: {created}")

    folders = note.get("folder_membership") or []
    if folders:
        folder_name = folders[0].get("name", "")
        if folder_name:
            lines.append(f"project: {slugify(folder_name)}")

    lines.append("source: Granola")
    lines.append("---")
    return "\n".join(lines)


def format_transcript(segments: list[dict]) -> str:
    """Merge consecutive same-speaker segments, then render as labelled dialogue."""
    if not segments:
        return ""

    utterances = []
    for seg in segments:
        source = (seg.get("speaker") or {}).get("source", "unknown")
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        if utterances and utterances[-1]["source"] == source:
            utterances[-1]["text"] += " " + text
        else:
            utterances.append({"source": source, "text": text})

    label_map = {"microphone": "**You**", "speaker": "**Them**"}

    lines = []
    for u in utterances:
        label = label_map.get(u["source"], f"**{u['source'].capitalize()}**")
        lines.append(f"{label}: {u['text']}\n")

    return "\n".join(lines)


def note_to_markdown(note: dict) -> str:
    parts = [format_front_matter(note)]

    title = note.get("title") or "Untitled"
    parts.append(f"\n# {title}\n")

    transcript = note.get("transcript") or []
    if transcript:
        parts.append("\n## Transcript\n")
        parts.append(format_transcript(transcript))

    return "\n".join(parts)


def md_filename(note: dict) -> str:
    created = (note.get("created_at") or "")[:10]
    title = note.get("title") or "Untitled"
    safe_title = re.sub(r":\s+", " — ", title).replace(":", "-")
    return f"{created} {safe_title}.md"


# --- Export ---

def export(api_key: str, output_dir: Path, skip_existing: bool) -> None:
    cache_dir = output_dir / ".cache"
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(exist_ok=True)

    print("Fetching note list...")
    notes = list_all_notes(api_key)
    print(f"Found {len(notes)} notes total.\n")

    (cache_dir / "manifest.json").write_text(json.dumps(notes, indent=2))

    failed = []
    for i, note in enumerate(notes, 1):
        note_id = note["id"]
        cache_path = cache_dir / f"{note_id}.json"

        if skip_existing and cache_path.exists():
            print(f"[{i}/{len(notes)}] Skipping (cached): {note.get('title', note_id)!r}")
            continue

        print(f"[{i}/{len(notes)}] Fetching: {note.get('title', note_id)!r}")
        try:
            full_note = get_note_with_transcript(api_key, note_id)
            cache_path.write_text(json.dumps(full_note, indent=2))
            (output_dir / md_filename(full_note)).write_text(note_to_markdown(full_note))
            time.sleep(REQUEST_DELAY)
        except urllib.error.HTTPError as e:
            print(f"  ERROR {e.code}: {e.reason}")
            failed.append(note_id)
            if e.code == 429:
                print("  Rate limited — waiting 10s...")
                time.sleep(10)

    print(f"\nDone. {len(notes) - len(failed)} exported, {len(failed)} failed.")
    if failed:
        print("Failed note IDs:", failed)


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Export Granola meeting transcripts as Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Set GRANOLA_API_KEY to your API key before running.",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Install the CLI and skill, then exit.",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write Markdown files (default: current directory)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Re-fetch and re-render all notes, ignoring the cache",
    )
    args = parser.parse_args()

    if args.setup:
        setup()
        return

    api_key = os.environ.get("GRANOLA_API_KEY")
    if not api_key:
        print("Error: GRANOLA_API_KEY environment variable not set.")
        print("Get your key from Granola → Settings → API → Create new key")
        sys.exit(1)

    export(
        api_key=api_key,
        output_dir=Path(args.output_dir),
        skip_existing=not args.overwrite,
    )


if __name__ == "__main__":
    main()
