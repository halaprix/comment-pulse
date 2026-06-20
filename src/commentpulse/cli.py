"""CLI for CommentPulse."""

import argparse
import sys

from .db import get_db, get_themes, get_comments, get_sources
from .importer import import_csv
from .clustering import cluster_comments
from .exporter import export_brief


def cmd_import(args):
    """Import comments from a CSV file."""
    conn = get_db(args.db)
    try:
        result = import_csv(conn, args.file, source_label=args.source, platform="csv")
        print(f"Imported {result['imported']} comments ({result['skipped']} skipped) "
              f"from '{result['title']}' → source_id={result['source_id']}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_themes(args):
    """Cluster comments into themes."""
    conn = get_db(args.db)
    try:
        themes = cluster_comments(conn, n_clusters=args.clusters, source_id=args.source)
        print(f"\nFound {len(themes)} themes:\n")
        for t in themes:
            print(f"  [{t['category']}] {t['label']}")
            print(f"    {t['comment_count']} comments, confidence={t.get('confidence', 0):.0%}")
            if t.get("top_terms"):
                print(f"    Terms: {', '.join(t['top_terms'])}")
            print()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_brief(args):
    """Export a Markdown brief."""
    conn = get_db(args.db)
    try:
        path = export_brief(conn, output_path=args.output)
        print(f"Brief exported to: {path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_list(args):
    """List sources or comments."""
    conn = get_db(args.db)
    try:
        if args.what == "sources":
            sources = get_sources(conn)
            if not sources:
                print("No sources found. Import a CSV first.")
                return
            print(f"\n{'ID':>4}  {'Platform':<10}  {'Title':<30}  {'Imported':<26}")
            print("-" * 76)
            for s in sources:
                print(f"{s['id']:>4}  {s['platform']:<10}  {s['title'][:30]:<30}  {s['imported_at'][:26]}")
        elif args.what == "comments":
            comments = get_comments(conn, source_id=args.source)
            if not comments:
                print("No comments found.")
                return
            print(f"\n{len(comments)} comments:")
            for c in comments[:20]:
                text = c["text"][:80] + "..." if len(c["text"]) > 80 else c["text"]
                print(f"  [{c['id']:>4}] {c.get('author','?')[:15]:<15}: {text}")
            if len(comments) > 20:
                print(f"  ...and {len(comments) - 20} more")
        elif args.what == "themes":
            themes = get_themes(conn)
            if not themes:
                print("No themes found. Run `commentpulse themes` first.")
                return
            print(f"\n{'ID':>4}  {'Category':<16}  {'Label':<30}  {'Count':>5}  {'Conf':>5}")
            print("-" * 68)
            for t in themes:
                print(f"{t['id']:>4}  {t['category']:<16}  {t['label'][:30]:<30}  "
                      f"{t['comment_count']:>5}  {t.get('confidence',0):>5.0%}")
    finally:
        conn.close()


def cmd_serve(args):
    """Start the web UI."""
    from .web import create_app
    conn = get_db(args.db)
    app = create_app(conn)
    print(f"CommentPulse running on http://localhost:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


def main():
    parser = argparse.ArgumentParser(
        prog="commentpulse",
        description="Turn creator comments into traceable pain points and content ideas.",
    )
    parser.add_argument("--db", default="commentpulse.db", help="SQLite database path")
    sub = parser.add_subparsers(dest="command")

    # import
    p_import = sub.add_parser("import", help="Import comments from CSV")
    p_import.add_argument("file", help="Path to CSV file")
    p_import.add_argument("--source", default="", help="Source label/title")
    p_import.set_defaults(func=cmd_import)

    # themes
    p_themes = sub.add_parser("themes", help="Cluster comments into themes")
    p_themes.add_argument("--clusters", type=int, default=5, help="Number of clusters")
    p_themes.add_argument("--source", type=int, default=None, help="Filter by source ID")
    p_themes.set_defaults(func=cmd_themes)

    # brief
    p_brief = sub.add_parser("brief", help="Export Markdown brief")
    p_brief.add_argument("--output", default="weekly-brief.md", help="Output file path")
    p_brief.set_defaults(func=cmd_brief)

    # list
    p_list = sub.add_parser("list", help="List sources, comments, or themes")
    p_list.add_argument("what", choices=["sources", "comments", "themes"],
                        help="What to list")
    p_list.add_argument("--source", type=int, default=None, help="Filter by source ID")
    p_list.set_defaults(func=cmd_list)

    # serve
    p_serve = sub.add_parser("serve", help="Start web UI")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=5000)
    p_serve.add_argument("--debug", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)
