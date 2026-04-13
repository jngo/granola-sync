#!/usr/bin/env python3
"""
Convert Granola exported JSON files to Markdown with YAML front matter.

Usage:
    python json_to_markdown.py [--input-dir ./granola_export] [--output-dir ./granola_markdown]

Output:
    One .md file per JSON file (manifest.json is skipped).
"""

import argparse
import json
import re
from pathlib import Path


def slugify(text: str) -> str:
    """Return a lowercase kebab-case slug from a string."""
    text = text.lower()
    text = text.replace(":", "-")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text


def iso_timestamp(raw: str) -> str:
    """Normalise an ISO datetime string to YYYY-MM-DDTHH:MM:SSZ, stripping milliseconds."""
    if not raw:
        return ""
    # Truncate to seconds and ensure Z suffix
    ts = raw[:19]
    if len(ts) == 19:
        return ts + "Z"
    return raw


def format_front_matter(note: dict) -> str:
    lines = ["---"]

    lines.append("type: transcript")

    created = iso_timestamp(note.get("created_at") or "")
    if created:
        lines.append(f"created: {created}")

    lines.append("status: closed")

    if created:
        lines.append(f"date: {created}")

    # project: first folder name slugified to kebab-case
    folders = note.get("folder_membership") or []
    if folders:
        folder_name = folders[0].get("name", "")
        if folder_name:
            lines.append(f"project: {slugify(folder_name)}")

    lines.append("source: Granola")

    lines.append("---")
    return "\n".join(lines)


def format_transcript(segments: list[dict]) -> str:
    """
    Merge consecutive segments from the same speaker, then render as a dialogue.
    Speaker sources:
      "microphone" → you (the note owner, recording locally)
      "speaker"    → the other participant(s) (captured via system audio)
    """
    if not segments:
        return ""

    # Merge consecutive same-speaker segments into utterances
    utterances = []
    for seg in segments:
        source = (seg.get("speaker") or {}).get("source", "unknown")
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        if utterances and utterances[-1]["source"] == source:
            utterances[-1]["text"] += " " + text
        else:
            utterances.append({"source": source, "text": text, "start": seg.get("start_time", "")})

    label_map = {
        "microphone": "**You**",
        "speaker": "**Them**",
    }

    lines = []
    for u in utterances:
        label = label_map.get(u["source"], f"**{u['source'].capitalize()}**")
        lines.append(f"{label}: {u['text']}\n")

    return "\n".join(lines)


def convert(note: dict) -> str:
    parts = []

    # Front matter
    parts.append(format_front_matter(note))

    # Title heading
    title = note.get("title") or "Untitled"
    parts.append(f"\n# {title}\n")

    # Transcript
    transcript = note.get("transcript") or []
    if transcript:
        parts.append("\n## Transcript\n")
        parts.append(format_transcript(transcript))

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Convert Granola JSON exports to Markdown.")
    parser.add_argument("--input-dir", default="./granola_export", help="Directory of JSON files")
    parser.add_argument("--output-dir", default="./granola_markdown", help="Directory for Markdown output")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing .md files")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(
        [f for f in input_dir.glob("*.json") if f.name != "manifest.json"]
    )
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return

    skipped = converted = 0
    for json_path in json_files:
        note = json.loads(json_path.read_text())
        created = (note.get("created_at") or "")[:10]
        title = note.get("title") or "Untitled"
        safe_title = re.sub(r":\s+", " — ", title).replace(":", "-")
        out_name = f"{created} {safe_title}.md"
        out_path = output_dir / out_name

        if out_path.exists() and not args.overwrite:
            skipped += 1
            continue

        out_path.write_text(convert(note))
        converted += 1
        print(f"Converted: {out_name}")

    print(f"\nDone. {converted} converted, {skipped} skipped.")


if __name__ == "__main__":
    main()
