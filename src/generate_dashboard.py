"""
generate_dashboard.py
Builds docs/index.html from summarized articles and saves a dated JSON archive.
"""

import os
import json
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
DATA_DIR = os.path.join(BASE_DIR, "data")

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI News Hub — Daily Digest</title>
<style>
  :root {{
    --bg: #0b0d12;
    --card: #151822;
    --text: #e8e9ed;
    --muted: #9a9fae;
    --accent: #7c9eff;
    --border: #232735;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 32px 16px 80px;
  }}
  .wrap {{ max-width: 760px; margin: 0 auto; }}
  header {{ margin-bottom: 28px; }}
  h1 {{ font-size: 26px; margin: 0 0 4px; }}
  .subtitle {{ color: var(--muted); font-size: 14px; }}
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
  }}
  .card h2 {{
    font-size: 16px;
    margin: 0 0 8px;
    line-height: 1.4;
  }}
  .card h2 a {{
    color: var(--text);
    text-decoration: none;
  }}
  .card h2 a:hover {{ color: var(--accent); }}
  .meta {{
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 10px;
  }}
  .summary {{
    font-size: 14px;
    line-height: 1.55;
    color: #cfd2dc;
  }}
  .empty {{
    text-align: center;
    color: var(--muted);
    padding: 60px 0;
  }}
  footer {{
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    margin-top: 32px;
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🧠 AI News Hub</h1>
    <div class="subtitle">Daily worldwide AI news digest — updated {updated_at}</div>
  </header>
  {content}
  <footer>Generated automatically · {count} stories today</footer>
</div>
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

EMPTY_TEMPLATE = """<div class="empty">No AI news found for today. Check back tomorrow.</div>"""


def format_date(iso_str):
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %H:%M UTC")
    except ValueError:
        return iso_str


def build_dashboard(articles):
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    # Save dated JSON archive
    archive_path = os.path.join(DATA_DIR, f"{date_str}.json")
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    # Build HTML content
    if not articles:
        content = EMPTY_TEMPLATE
    else:
        content = "".join(
            CARD_TEMPLATE.format(
                url=a["url"],
                title=a["title"],
                source=a["source"],
                published=format_date(a.get("published", "")),
                summary=a.get("summary", ""),
            )
            for a in articles
        )

    html = PAGE_TEMPLATE.format(
        updated_at=now.strftime("%b %d, %Y %H:%M UTC"),
        content=content,
        count=len(articles),
    )

    index_path = os.path.join(DOCS_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard written to {index_path}")
    print(f"Archive written to {archive_path}")


if __name__ == "__main__":
    build_dashboard([])
