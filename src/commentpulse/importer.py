"""CSV import for CommentPulse."""

import csv
import sqlite3
from pathlib import Path
from typing import Optional

from .db import add_source, add_comment


REQUIRED_COLS = {"text"}
OPTIONAL_COLS = {"author", "timestamp", "comment_id", "permalink", "source_url", "title"}


def import_csv(conn: sqlite3.Connection, csv_path: str, source_label: str = "",
               platform: str = "csv") -> dict:
    """Import comments from a CSV file into the database.

    Expected columns (minimum): text
    Optional columns: author, timestamp, comment_id, permalink, source_url, title

    Returns a dict with import stats.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    title = source_label or path.stem
    source_id = add_source(conn, platform=platform, title=title)

    imported = 0
    skipped = 0

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("CSV has no header row")

        # Normalize field names (case-insensitive)
        fieldmap = {}
        for field in reader.fieldnames:
            lower = field.strip().lower()
            fieldmap[lower] = field

        if "text" not in fieldmap and "comment" not in fieldmap and "message" not in fieldmap:
            raise ValueError(
                f"CSV must have a 'text' column (or 'comment'/'message'). "
                f"Found columns: {reader.fieldnames}"
            )

        text_key = fieldmap.get("text") or fieldmap.get("comment") or fieldmap.get("message")

        for row in reader:
            text = (row.get(text_key) or "").strip()
            if not text:
                skipped += 1
                continue

            author = (row.get(fieldmap.get("author", "")) or "").strip()
            timestamp = (row.get(fieldmap.get("timestamp", "")) or "").strip()
            external_id = (row.get(fieldmap.get("comment_id", "")) or "").strip()
            permalink = (row.get(fieldmap.get("permalink", "")) or "").strip()

            add_comment(
                conn,
                source_id=source_id,
                text=text,
                author=author,
                external_id=external_id,
                timestamp=timestamp,
                permalink=permalink,
            )
            imported += 1

    return {
        "source_id": source_id,
        "imported": imported,
        "skipped": skipped,
        "title": title,
    }
