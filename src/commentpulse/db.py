"""SQLite database layer for CommentPulse."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    source_url TEXT,
    title TEXT,
    imported_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    external_id TEXT,
    author TEXT,
    text TEXT NOT NULL,
    timestamp TEXT,
    permalink TEXT,
    theme_id INTEGER,
    FOREIGN KEY (source_id) REFERENCES sources(id),
    FOREIGN KEY (theme_id) REFERENCES themes(id)
);

CREATE TABLE IF NOT EXISTS themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    category TEXT NOT NULL,
    summary TEXT,
    confidence REAL DEFAULT 0.0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_comments_source ON comments(source_id);
CREATE INDEX IF NOT EXISTS idx_comments_theme ON comments(theme_id);
"""


def get_db(db_path: str = "commentpulse.db") -> sqlite3.Connection:
    """Open or create the SQLite database with the CommentPulse schema."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_source(conn: sqlite3.Connection, platform: str, source_url: str = "",
               title: str = "") -> int:
    """Insert a source record and return its ID."""
    now = datetime.utcnow().isoformat()
    cur = conn.execute(
        "INSERT INTO sources (platform, source_url, title, imported_at) VALUES (?, ?, ?, ?)",
        (platform, source_url, title, now),
    )
    conn.commit()
    return cur.lastrowid


def add_comment(conn: sqlite3.Connection, source_id: int,
                text: str, author: str = "", external_id: str = "",
                timestamp: str = "", permalink: str = "") -> int:
    """Insert a comment record and return its ID."""
    cur = conn.execute(
        """INSERT INTO comments
        (source_id, external_id, author, text, timestamp, permalink)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (source_id, external_id, author, text, timestamp, permalink),
    )
    conn.commit()
    return cur.lastrowid


def add_theme(conn: sqlite3.Connection, label: str, category: str,
              summary: str = "", confidence: float = 0.0) -> int:
    """Insert a theme record and return its ID."""
    now = datetime.utcnow().isoformat()
    cur = conn.execute(
        """INSERT INTO themes (label, category, summary, confidence, created_at)
        VALUES (?, ?, ?, ?, ?)""",
        (label, category, summary, confidence, now),
    )
    conn.commit()
    return cur.lastrowid


def assign_theme(conn: sqlite3.Connection, comment_id: int, theme_id: int):
    """Assign a theme to a comment."""
    conn.execute(
        "UPDATE comments SET theme_id = ? WHERE id = ?",
        (theme_id, comment_id),
    )
    conn.commit()


def get_comments(conn: sqlite3.Connection, source_id: Optional[int] = None) -> list[dict]:
    """Retrieve comments, optionally filtered by source."""
    if source_id:
        rows = conn.execute(
            "SELECT * FROM comments WHERE source_id = ? ORDER BY id",
            (source_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM comments ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def get_themes(conn: sqlite3.Connection) -> list[dict]:
    """Retrieve all themes with comment counts."""
    rows = conn.execute(
        """SELECT t.*, COUNT(c.id) as comment_count
        FROM themes t
        LEFT JOIN comments c ON c.theme_id = t.id
        GROUP BY t.id
        ORDER BY comment_count DESC, t.id"""
    ).fetchall()
    return [dict(r) for r in rows]


def get_comments_by_theme(conn: sqlite3.Connection, theme_id: int) -> list[dict]:
    """Retrieve all comments assigned to a theme."""
    rows = conn.execute(
        "SELECT * FROM comments WHERE theme_id = ? ORDER BY id",
        (theme_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_sources(conn: sqlite3.Connection) -> list[dict]:
    """Retrieve all sources."""
    rows = conn.execute(
        "SELECT * FROM sources ORDER BY imported_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]
