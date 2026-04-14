#!/usr/bin/env python3
"""
Export Granola meeting transcripts as Markdown to a local directory.

Usage:
    GRANOLA_API_KEY=grn_... python granola.py [--output-dir /path/to/vault/transcripts]

JSON responses are cached in <output-dir>/.cache/ keyed by note ID.
Delete a note's cache file to force a re-fetch and re-render.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests")
    sys.exit(1)


BASE_URL = "https://public-api.granola.ai"
REQUEST_DELAY = 0.25  # seconds between requests; burst: 25 req/5s, sustained: 5 req/s


# --- API ---

def get_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def list_all_notes(api_key: str) -> list[dict]:
    """Paginate through all notes and return a flat list of note summaries."""
    notes = []
    cursor = None
    page = 1

    while True:
        params = {"page_size": 30}
        if cursor:
            params["cursor"] = cursor

        resp = requests.get(
            f"{BASE_URL}/v1/notes",
            headers=get_headers(api_key),
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

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
    resp = requests.get(
        f"{BASE_URL}/v1/notes/{note_id}",
        headers=get_headers(api_key),
        params={"include": "transcript"},
    )
    resp.raise_for_status()
    return resp.json()


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
        except requests.HTTPError as e:
            print(f"  ERROR {e.response.status_code}: {e}")
            failed.append(note_id)
            if e.response.status_code == 429:
                print("  Rate limited — waiting 10s...")
                time.sleep(10)

    print(f"\nDone. {len(notes) - len(failed)} exported, {len(failed)} failed.")
    if failed:
        print("Failed note IDs:", failed)


def main():
    parser = argparse.ArgumentParser(
        description="Export Granola meeting transcripts as Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Set GRANOLA_API_KEY to your API key before running.",
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
