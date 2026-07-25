"""
generate_dashboard.py
Builds docs/index.html (today's digest) and a full browsable archive of
past days at docs/archive/. Includes a visitor-controlled light/dark
theme toggle (saved in the browser via localStorage).
"""

import os
import json
import glob
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
ARCHIVE_DIR = os.path.join(DOCS_DIR, "archive")
DATA_DIR = os.path.join(BASE_DIR, "data")

STYLE_AND_SCRIPT = """
<style>
  :root {
    --bg: #0b0d12;
    --card: #151822;
    --text: #e8e9ed;
    --muted: #9a9fae;
    --accent: #7c9eff;
    --border: #232735;
  }
  html.light {
    --bg: #f6f7fb;
    --card: #ffffff;
    --text: #16181f;
    --muted: #666b78;
    --accent: #3f5fd8;
    --border: #e4e6ed;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 32px 16px 80px;
    transition: background 0.2s ease, color 0.2s ease;
  }
  .wrap { max-width: 760px; margin: 0 auto; }
  header { margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
  h1 { font-size: 26px; margin: 0 0 4px; }
  .subtitle { color: var(--muted); font-size: 14px; }
  .nav-links { font-size: 13px; margin-top: 10px; }
  .nav-links a { color: var(--accent); text-decoration: none; margin-right: 14px; }
  .nav-links a:hover { text-decoration: underline; }
  .theme-toggle {
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    cursor: pointer;
    white-space: nowrap;
  }
  .theme-toggle:hover { border-color: var(--accent); }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
  }
  .card h2 { font-size: 16px; margin: 0 0 8px; line-height: 1.4; }
  .card h2 a { color: var(--text); text-decoration: none; }
  .card h2 a:hover { color: var(--accent); }
  .meta { font-size: 12px; color: var(--muted); margin-bottom: 10px; }
  .summary { font-size: 14px; line-height: 1.55; color: var(--text); opacity: 0.85; }
  .empty { text-align: center; color: var(--muted); padding: 60px 0; }
  .archive-list { list-style: none; padding: 0; margin: 0; }
  .archive-list li { margin-bottom: 8px; }
  .archive-list a {
    display: block;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
    color: var(--text);
    text-decoration: none;
    font-size: 14px;
  }
  .archive-list a:hover { border-color: var(--accent); }
  footer { text-align: center; color: var(--muted); font-size: 12px; margin-top: 32px; }
</style>
<script>
  (function() {
    var saved = localStorage.getItem('ai-news-theme');
    if (saved === 'light') document.documentElement.classList.add('light');
  })();
</script>
"""

TOGGLE_SCRIPT = """
<script>
  function toggleTheme() {
    var html = document.documentElement;
    html.classList.toggle('light');
    localStorage.setItem('ai-news-theme', html.classList.contains('light') ? 'light' : 'dark');
  }
</script>
"""

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title}</title>
{style}
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>🧠 AI News Hub</h1>
      <div class="subtitle">{subtitle}</div>
      <div class="nav-links">{nav_links}</div>
    </div>
    <button class="theme-toggle" onclick="toggleTheme()">☀️ / 🌙 Toggle theme</button>
  </header>
  {content}
  <footer>{footer}</footer>
</div>
{toggle_script}
</body>
</html>
"""

CARD_TEMPLATE = """
  <div class="card">
    <h2><a href="{url}" target="_blank" rel="noopener">{title}</a></h2>
    <div class="meta">{source} · {published}</div>
    <div class="summary">{summary}</div>
  </div>
"""

EMPTY_TEMPLATE = """<div class="empty">No AI news found for this day.</div>"""


def format_date(iso_str):
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %H:%M UTC")
    except ValueError:
        return iso_str


def render_articles(articles):
    if not articles:
        return EMPTY_TEMPLATE
    return "".join(
        CARD_TEMPLATE.format(
            url=a["url"],
            title=a["title"],
            source=a["source"],
            published=format_date(a.get("published", "")),
            summary=a.get("summary", ""),
        )
        for a in articles
    )


def render_page(page_title, subtitle, nav_links, content, footer):
    return PAGE_TEMPLATE.format(
        page_title=page_title,
        style=STYLE_AND_SCRIPT,
        subtitle=subtitle,
        nav_links=nav_links,
        content=content,
        footer=footer,
        toggle_script=TOGGLE_SCRIPT,
    )


def build_archive():
    """Rebuilds a page for every past day found in data/, plus an archive index."""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    json_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.json")), reverse=True)
    date_entries = []

    for path in json_files:
        date_str = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path, "r", encoding="utf-8") as f:
                articles = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        date_entries.append((date_str, len(articles)))

        content = render_articles(articles)
        html = render_page(
            page_title=f"AI News Hub — {date_str}",
            subtitle=f"Digest for {date_str}",
            nav_links='<a href="../index.html">← Today</a><a href="index.html">All days</a>',
            content=content,
            footer=f"{len(articles)} stories on {date_str}",
        )
        with open(os.path.join(ARCHIVE_DIR, f"{date_str}.html"), "w", encoding="utf-8") as f:
            f.write(html)

    if date_entries:
        list_items = "".join(
            f'<li><a href="{date_str}.html">{date_str} — {count} stories</a></li>'
            for date_str, count in date_entries
        )
        archive_content = f'<ul class="archive-list">{list_items}</ul>'
    else:
        archive_content = EMPTY_TEMPLATE

    archive_html = render_page(
        page_title="AI News Hub — Archive",
        subtitle="Every past daily digest",
        nav_links='<a href="../index.html">← Back to today</a>',
        content=archive_content,
        footer=f"{len(date_entries)} days archived",
    )
    with open(os.path.join(ARCHIVE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(archive_html)


def build_dashboard(articles):
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    archive_path = os.path.join(DATA_DIR, f"{date_str}.json")
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    content = render_articles(articles)
    html = render_page(
        page_title="AI News Hub — Daily Digest",
        subtitle=f"Daily worldwide AI news digest — updated {now.strftime('%b %d, %Y %H:%M UTC')}",
        nav_links='<a href="archive/index.html">📚 View past days</a>',
        content=content,
        footer=f"Generated automatically · {len(articles)} stories today",
    )
    index_path = os.path.join(DOCS_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    build_archive()

    print(f"Dashboard written to {index_path}")
    print(f"Archive written to {archive_path}")
    print(f"Archive pages rebuilt in {ARCHIVE_DIR}")


if __name__ == "__main__":
    build_dashboard([])
