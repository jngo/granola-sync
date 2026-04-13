#!/usr/bin/env python3
"""
Export all meeting transcripts from Granola API.

Usage:
    GRANOLA_API_KEY=grn_... python export_transcripts.py [--output-dir ./transcripts]

Output:
    One JSON file per meeting in the output directory.
    A combined manifest (manifest.json) with all note summaries.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests")
    sys.exit(1)


BASE_URL = "https://public-api.granola.ai"
# Burst: 25 req / 5s, sustained: 5 req/s. Stay comfortably under both.
REQUEST_DELAY = 0.25  # seconds between requests


def get_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def list_all_notes(api_key: str) -> list[dict]:
    """Paginate through all notes and return a list of note summaries."""
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


def safe_filename(note: dict) -> str:
    """Build a filesystem-safe filename from note metadata."""
    created = note.get("created_at", "")[:10]  # YYYY-MM-DD
    title = note.get("title") or note.get("id", "untitled")
    safe = "".join(c if c.isalnum() or c in " -_." else "_" for c in title)
    safe = safe.strip().rstrip(".")[:80]
    return f"{created}_{safe}_{note['id']}.json"


def export(api_key: str, output_dir: Path, skip_existing: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching note list...")
    notes = list_all_notes(api_key)
    print(f"Found {len(notes)} notes total.\n")

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(notes, indent=2))
    print(f"Manifest written to {manifest_path}\n")

    failed = []
    for i, note in enumerate(notes, 1):
        note_id = note["id"]
        filename = safe_filename(note)
        out_path = output_dir / filename

        if skip_existing and out_path.exists():
            print(f"[{i}/{len(notes)}] Skipping (already exists): {filename}")
            continue

        print(f"[{i}/{len(notes)}] Fetching: {note.get('title', note_id)!r}")
        try:
            full_note = get_note_with_transcript(api_key, note_id)
            out_path.write_text(json.dumps(full_note, indent=2))
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
    parser = argparse.ArgumentParser(description="Export all Granola transcripts.")
    parser.add_argument(
        "--output-dir",
        default="./granola_export",
        help="Directory to write exported files (default: ./granola_export)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip notes already exported (default: true)",
    )
    parser.add_argument(
        "--no-skip-existing",
        dest="skip_existing",
        action="store_false",
        help="Re-download and overwrite existing files",
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
        skip_existing=args.skip_existing,
    )


if __name__ == "__main__":
    main()
