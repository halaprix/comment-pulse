# SPEC — CommentPulse

## User story

As a small creator, I want to turn audience comments into traceable pain-point clusters, so that I can plan useful content without manually reading hundreds of comments.

## Core flow

1. User pastes a public video URL or uploads a CSV of comments.
2. The app imports comment text, author handle, timestamp, and source ID/link where available.
3. The app groups comments into themes: questions, pains, objections, praise, and urgent-support signals.
4. The user reviews a dashboard of themes with representative comments.
5. The user exports a weekly brief with content ideas and original evidence links.

## Data model

- `Source`: platform, source URL, imported at, title.
- `Comment`: source ID, external ID, author label, text, timestamp, permalink/comment URL.
- `Theme`: label, category, summary, confidence, representative comment IDs.
- `Brief`: date range, selected themes, generated recommendations, export format.

## Technical approach

- Start as a small web app with a local-first import path: CSV upload first, YouTube API later.
- Store imported comments in SQLite.
- Use deterministic preprocessing for deduplication and language detection.
- Use an LLM only for classification and summary generation, always preserving original comment references.
- Export Markdown first; PDF can be generated from the Markdown artifact.

## Validation plan

- Run the tool on public comment exports from 3–5 creators or sample datasets.
- Check whether generated themes map back to real comment IDs.
- Ask creators whether the weekly brief produces at least three usable content ideas.
- Measure time-to-brief versus manual comment review.

## Milestones

- v0.1.0-alpha.0 — repo scaffold and product spec.
- v0.1.0-alpha.1 — CSV import, SQLite storage, theme clustering stub.
- v0.2.0-alpha.1 — usable demo with Markdown export and traceable evidence.
