# CommentPulse — v0.1.0-alpha.1

Turn creator comments into traceable audience pain points and content ideas.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
commentpulse import comments.csv --source "My Video"
commentpulse themes
commentpulse brief --output weekly-brief.md
```

## MVP scope

- CSV comment import (author, text, timestamp, comment_id, permalink)
- SQLite storage with source traceability
- Deterministic theme clustering (keyword + TF-IDF)
- Markdown brief export with evidence links
- Web UI for browsing themes and comments

## Tech stack

- Python 3.11+, SQLite, Flask
- scikit-learn (TF-IDF + clustering)
- No LLM dependency for MVP — deterministic clustering first
