#!/usr/bin/env python3
"""Generate root index.html from article metadata."""

import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

SCRIPT_DIR = Path(__file__).parent
ARTICLES_DIR = SCRIPT_DIR / "articles"


def extract_abstract(tex_path):
    """Extract abstract from main.tex, convert LaTeX to approximate HTML with paragraphs."""
    content = tex_path.read_text()
    start = content.find(r'\begin{abstract}')
    end = content.find(r'\end{abstract}')
    if start == -1 or end == -1:
        return ""

    raw = content[start + len(r'\begin{abstract}'):end]

    # Convert text formatting to HTML
    raw = re.sub(r'\\textit\{([^}]+)\}', r'<em>\1</em>', raw)
    raw = re.sub(r'\\textbf\{([^}]+)\}', r'<strong>\1</strong>', raw)

    # Strip footnotes and citations
    raw = re.sub(r'\\footnote\{[^}]*\}', '', raw)
    raw = re.sub(r'\\footcite\[([^\]]*)\]\{[^}]*\}', '', raw)
    raw = re.sub(r'\\footcite\{[^}]*\}', '', raw)
    raw = re.sub(r'\\cite\{[^}]*\}', '', raw)

    # Strip other LaTeX commands
    raw = re.sub(r'\\newline', ' ', raw)
    raw = re.sub(r'\\noindent', '', raw)
    raw = re.sub(r'\\\\', ' ', raw)
    raw = re.sub(r'---', '&mdash;', raw)
    raw = re.sub(r"``|''", '"', raw)
    raw = re.sub(r"`([^']*)'", r'"\1"', raw)

    # Preserve paragraph breaks (blank lines in LaTeX = paragraph break)
    paragraphs = re.split(r'\n\s*\n', raw)
    cleaned = []
    for p in paragraphs:
        p = re.sub(r'\s+', ' ', p).strip()
        if p:
            cleaned.append(f'<p>{p}</p>')

    return ''.join(cleaned)


def format_date(date_str):
    """Format ISO date to display format."""
    dt = datetime.strptime(str(date_str), '%Y-%m-%d')
    return dt.strftime('%B %d, %Y')


def collect_articles():
    """Collect all published articles with metadata."""
    articles = []
    tag_counts = {}
    for article_dir in sorted(ARTICLES_DIR.iterdir()):
        if not article_dir.is_dir():
            continue

        metadata_path = article_dir / "metadata.yaml"
        if not metadata_path.exists():
            continue

        meta = yaml.safe_load(metadata_path.read_text())
        if meta.get('status') != 'published':
            continue

        # Extract abstract from main.tex
        tex_path = article_dir / "main.tex"
        if tex_path.exists():
            meta['abstract'] = extract_abstract(tex_path)
        else:
            meta['abstract'] = ""

        meta['url'] = f"articles/{article_dir.name}/"
        meta['display_date'] = format_date(meta['date'])
        meta['dir_name'] = article_dir.name
        articles.append(meta)

        for tag in meta.get('tags', []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Sort by date descending
    articles.sort(key=lambda a: a['date'], reverse=True)

    # Sort tags alphabetically
    sorted_tags = [{'name': t, 'count': c} for t, c in sorted(tag_counts.items())]
    return articles, sorted_tags


def generate_index(articles, tags):
    """Generate root index.html."""
    env = Environment(loader=FileSystemLoader(str(SCRIPT_DIR)))
    template = env.get_template("index-template.html.j2")
    html = template.render(
        articles=json.dumps(articles, default=str),
        tags=json.dumps(tags, default=str)
    )
    (SCRIPT_DIR / "index.html").write_text(html)
    print(f"Generated index.html ({len(articles)} articles, {len(tags)} tags)")


if __name__ == '__main__':
    articles, tags = collect_articles()
    generate_index(articles, tags)
