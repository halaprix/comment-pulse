# CommentPulse

Turn creator comments into traceable audience pain points and content ideas.

## Problem

Creators get useful audience signals in comments, but the important questions and pain points are buried under noisy engagement metrics. Existing analytics emphasize views, CTR, watch time, and revenue; they usually do not answer: “what are people repeatedly struggling with, and where is the original evidence?”

## Evidence

| Source | Link | Signal |
|---|---|---|
| Reddit / r/SideProject | https://www.reddit.com/r/SideProject/comments/1ua8uk2/i_built_an_automation_that_tells_a_youtube/ | A builder reports that repeated audience questions were buried in comments and that traceable comment IDs made AI-generated insights more useful. |
| Reddit / r/SideProject | https://www.reddit.com/r/SideProject/comments/1ua9ayc/built_a_financial_dashboard_for_creators_selling/ | Creator tooling pain repeats across platforms: single-platform dashboards do not show the combined reality creators care about. |
| Reddit / r/productivity | https://www.reddit.com/r/productivity/comments/1ua79pm/how_do_i_stop_getting_distracted_online_and/ | Public thread shows people asking for practical systems around focus and online work; comment mining can reveal recurring content topics. |

## Target user

Small YouTube/newsletter/course creators who already have an audience but do not have a research assistant, community manager, or analytics team.

## MVP

- Import comments from a YouTube video URL or CSV export.
- Cluster comments into repeated pains, questions, objections, and urgent-support flags.
- Show every generated insight with links or IDs back to original comments.
- Export a weekly Markdown/PDF brief with content ideas and evidence snippets.

## Non-goals

- No auto-replies or audience engagement automation.
- No scraping behind login walls.
- No claim that AI classification is authoritative; it is a triage layer.
- No multi-platform integrations until the YouTube/CSV flow is useful.

## Status

v0.1.0-alpha.0 — scaffold/spec only.
