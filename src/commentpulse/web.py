"""Flask web UI for CommentPulse."""

import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, flash

from .db import (
    get_sources, get_comments, get_themes, get_comments_by_theme,
)
from .importer import import_csv
from .clustering import cluster_comments


HTML_BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CommentPulse</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #f8f9fa; color: #1a1a2e; line-height: 1.6; }
  .container { max-width: 960px; margin: 0 auto; padding: 20px; }
  h1 { font-size: 1.8rem; margin-bottom: 8px; }
  h2 { font-size: 1.3rem; margin: 20px 0 10px; }
  a { color: #4361ee; text-decoration: none; }
  a:hover { text-decoration: underline; }
  nav { display: flex; gap: 16px; margin-bottom: 20px; padding: 12px 0;
        border-bottom: 1px solid #e0e0e0; }
  nav a { font-weight: 500; }
  .card { background: white; border: 1px solid #e0e0e0; border-radius: 8px;
          padding: 16px; margin-bottom: 12px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px;
           font-size: 0.8rem; font-weight: 600; }
  .badge-question { background: #e7f5ff; color: #1971c2; }
  .badge-pain { background: #fff4e6; color: #e8590c; }
  .badge-objection { background: #fff0f0; color: #c92a2a; }
  .badge-praise { background: #ebfbee; color: #2b8a3e; }
  .badge-urgent-support { background: #fce4d6; color: #c92a2a; }
  .badge-general { background: #f1f3f5; color: #495057; }
  .meta { font-size: 0.85rem; color: #666; margin-top: 4px; }
  .comment { padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
  .comment:last-child { border-bottom: none; }
  .comment .author { font-weight: 600; font-size: 0.9rem; }
  .comment .text { margin: 4px 0; }
  .comment .link { font-size: 0.8rem; }
  table { width: 100%; border-collapse: collapse; margin: 10px 0; }
  th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #e0e0e0; }
  th { font-weight: 600; background: #f8f9fa; }
  .flash { background: #d4edda; color: #155724; padding: 10px 16px;
           border-radius: 6px; margin-bottom: 16px; }
  form { margin: 16px 0; }
  input[type=file], input[type=text] { padding: 8px; border: 1px solid #ccc;
         border-radius: 4px; margin-right: 8px; }
  button { padding: 8px 16px; background: #4361ee; color: white; border: none;
           border-radius: 4px; cursor: pointer; }
  button:hover { background: #3a56d4; }
  .conf { font-size: 0.8rem; color: #888; }
  .actions { margin: 16px 0; display: flex; gap: 12px; }
</style>
</head>
<body>
<div class="container">
  <h1>📡 CommentPulse</h1>
  <p class="meta">Turn creator comments into traceable pain points and content ideas.</p>
  <nav>
    <a href="/">Dashboard</a>
    <a href="/sources">Sources</a>
    <a href="/themes">Themes</a>
    <a href="/import">Import</a>
  </nav>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for m in messages %}
        <div class="flash">{{ m }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</div>
</body>
</html>
"""

HTML_DASHBOARD = """
{% extends "base" %}
{% block content %}
  <h2>Dashboard</h2>
  <div class="card">
    <strong>{{ sources|length }}</strong> sources ·
    <strong>{{ themes|length }}</strong> themes ·
    <strong>{{ comment_count }}</strong> comments
  </div>
  {% if themes %}
    <h2>Top Themes</h2>
    {% for t in themes[:5] %}
      <div class="card">
        <span class="badge badge-{{ t.category }}">{{ t.category }}</span>
        <strong>{{ t.label }}</strong>
        <span class="conf">· {{ t.comment_count }} comments · {{ '%d%%'|format(t.confidence*100) if t.confidence else '—' }}</span>
        <p class="meta">{{ t.summary or '' }}</p>
        <a href="/themes/{{ t.id }}">View evidence →</a>
      </div>
    {% endfor %}
  {% else %}
    <div class="card">
      No themes yet. <a href="/import">Import a CSV</a> then run clustering.
    </div>
  {% endif %}
{% endblock %}
"""

HTML_SOURCES = """
{% extends "base" %}
{% block content %}
  <h2>Sources</h2>
  {% if sources %}
    <table>
      <tr><th>ID</th><th>Platform</th><th>Title</th><th>Imported</th><th>Comments</th></tr>
      {% for s in sources %}
        <tr>
          <td>{{ s.id }}</td>
          <td>{{ s.platform }}</td>
          <td>{{ s.title }}</td>
          <td class="meta">{{ s.imported_at[:19] }}</td>
          <td>{{ s.comment_count or '—' }}</td>
        </tr>
      {% endfor %}
    </table>
  {% else %}
    <div class="card">No sources yet. <a href="/import">Import a CSV</a> first.</div>
  {% endif %}
{% endblock %}
"""

HTML_THEMES = """
{% extends "base" %}
{% block content %}
  <h2>Themes</h2>
  <div class="actions">
    <form method="post" action="/themes/cluster">
      <button type="submit">Re-cluster comments</button>
    </form>
  </div>
  {% if themes %}
    {% for t in themes %}
      <div class="card">
        <span class="badge badge-{{ t.category }}">{{ t.category }}</span>
        <strong>{{ t.label }}</strong>
        <span class="conf">· {{ t.comment_count }} comments · {{ '%d%%'|format(t.confidence*100) if t.confidence else '—' }}</span>
        <p class="meta">{{ t.summary or '' }}</p>
        <a href="/themes/{{ t.id }}">View evidence →</a>
      </div>
    {% endfor %}
  {% else %}
    <div class="card">No themes yet. Click "Re-cluster" to generate.</div>
  {% endif %}
{% endblock %}
"""

HTML_THEME_DETAIL = """
{% extends "base" %}
{% block content %}
  <h2><span class="badge badge-{{ theme.category }}">{{ theme.category }}</span> {{ theme.label }}</h2>
  <p class="meta">{{ theme.summary or '' }}</p>
  <p class="conf">{{ comments|length }} comments · confidence: {{ '%d%%'|format(theme.confidence*100) if theme.confidence else '—' }}</p>
  <h3>Evidence</h3>
  {% for c in comments %}
    <div class="comment">
      <div class="author">{{ c.author or 'anonymous' }}</div>
      <div class="text">{{ c.text }}</div>
      {% if c.permalink %}
        <div class="link"><a href="{{ c.permalink }}" target="_blank">→ original comment</a></div>
      {% endif %}
    </div>
  {% else %}
    <p class="meta">No comments assigned to this theme.</p>
  {% endfor %}
{% endblock %}
"""

HTML_IMPORT = """
{% extends "base" %}
{% block content %}
  <h2>Import Comments</h2>
  <div class="card">
    <p>Upload a CSV file with comments. Required column: <code>text</code>. 
       Optional: <code>author</code>, <code>timestamp</code>, <code>comment_id</code>, <code>permalink</code>.</p>
    <form method="post" action="/import" enctype="multipart/form-data">
      <input type="text" name="source" placeholder="Source label (optional)">
      <input type="file" name="csvfile" accept=".csv" required>
      <button type="submit">Import</button>
    </form>
  </div>
  {% if sources %}
    <h3>Existing sources</h3>
    <table>
      <tr><th>ID</th><th>Title</th><th>Imported</th></tr>
      {% for s in sources %}
        <tr><td>{{ s.id }}</td><td>{{ s.title }}</td><td class="meta">{{ s.imported_at[:19] }}</td></tr>
      {% endfor %}
    </table>
  {% endif %}
{% endblock %}
"""


def create_app(conn: sqlite3.Connection) -> Flask:
    """Create and configure the Flask app with a shared DB connection."""
    app = Flask(__name__)
    app.secret_key = "commentpulse-dev-key"

    @app.template_filter("base")
    def render_base(content, **ctx):
        return render_template_string(HTML_BASE, **ctx)

    # Custom template rendering: we use a simple extends pattern
    # Flask's render_template_string doesn't support our "base" block well,
    # so we manually compose.

    def render_page(template_name: str, **ctx) -> str:
        """Compose a page by injecting the content block into the base template."""
        # Find the content block in the named template
        from jinja2 import Environment, Template
        env = app.jinja_env

        # Simple approach: render the content template to get its body
        full_template = HTML_BASE.replace(
            "{% block content %}{% endblock %}",
            _extract_content_block(template_name)
        )
        return env.from_string(full_template).render(**ctx)

    @app.route("/")
    def dashboard():
        from .db import get_sources, get_themes, get_comments
        sources = get_sources(conn)
        themes = get_themes(conn)
        comments = get_comments(conn)
        return render_page("dashboard", sources=sources, themes=themes,
                          comment_count=len(comments))

    @app.route("/sources")
    def sources():
        from .db import get_sources
        srcs = get_sources(conn)
        return render_page("sources", sources=srcs)

    @app.route("/themes")
    def themes():
        from .db import get_themes
        ths = get_themes(conn)
        return render_page("themes", themes=ths)

    @app.route("/themes/<int:theme_id>")
    def theme_detail(theme_id: int):
        from .db import get_themes, get_comments_by_theme
        themes = get_themes(conn)
        theme = next((t for t in themes if t["id"] == theme_id), None)
        if not theme:
            return "Theme not found", 404
        comments = get_comments_by_theme(conn, theme_id)
        return render_page("theme_detail", theme=theme, comments=comments)

    @app.route("/themes/cluster", methods=["POST"])
    def do_cluster():
        cluster_comments(conn)
        flash("Re-clustered comments into themes.")
        return redirect(url_for("themes"))

    @app.route("/import", methods=["GET", "POST"])
    def import_page():
        from .db import get_sources
        if request.method == "POST":
            file = request.files.get("csvfile")
            if not file:
                flash("No file uploaded.")
                return redirect(url_for("import_page"))
            import tempfile, os
            tmp_path = os.path.join(tempfile.gettempdir(), f"cp_import_{os.getpid()}.csv")
            file.save(tmp_path)
            try:
                result = import_csv(conn, tmp_path,
                                    source_label=request.form.get("source", ""))
                flash(f"Imported {result['imported']} comments from '{result['title']}'")
            except Exception as e:
                flash(f"Import error: {e}")
            finally:
                os.unlink(tmp_path)
            return redirect(url_for("import_page"))
        srcs = get_sources(conn)
        return render_page("import", sources=srcs)

    return app


# Template content blocks keyed by name
_CONTENT_BLOCKS = {
    "dashboard": HTML_DASHBOARD,
    "sources": HTML_SOURCES,
    "themes": HTML_THEMES,
    "theme_detail": HTML_THEME_DETAIL,
    "import": HTML_IMPORT,
}


def _extract_content_block(name: str) -> str:
    """Get the content block HTML for a named template."""
    raw = _CONTENT_BLOCKS.get(name, "")
    # Strip Jinja extends/block tags — we just want the inner content
    import re
    raw = re.sub(r'{%\s*extends[^%]*%}', '', raw)
    raw = re.sub(r'{%\s*block\s+content\s*%}', '', raw)
    raw = re.sub(r'{%\s*endblock\s*%}', '', raw)
    return raw.strip()
