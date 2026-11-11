#!/usr/bin/env python3
"""Generate root index.html from article metadata."""

import os
import re
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader

SCRIPT_DIR = Path(__file__).parent
ARTICLES_DIR = SCRIPT_DIR / "articles"


def strip_command(text, command):
    """Remove every ``\command[opt]{arg}`` occurrence, handling nested braces.

    The command name must not run into further letters, so ``cite`` will not
    match ``\citet``.
    """
    pattern = re.compile(r'\\' + command + r'(?![A-Za-z])')
    out = []
    i = 0
    while True:
        match = pattern.search(text, i)
        if not match:
            out.append(text[i:])
            break

        start = match.start()
        pos = match.end()

        # Skip an optional argument such as \footcite[...]{...}
        while pos < len(text) and text[pos] == '[':
            depth = 0
            while pos < len(text):
                if text[pos] == '[':
                    depth += 1
                elif text[pos] == ']':
                    depth -= 1
                    if depth == 0:
                        pos += 1
                        break
                pos += 1

        if pos < len(text) and text[pos] == '{':
            depth = 0
            while pos < len(text):
                if text[pos] == '{':
                    depth += 1
                elif text[pos] == '}':
                    depth -= 1
                    if depth == 0:
                        pos += 1
                        break
                pos += 1
            out.append(text[i:start])
            i = pos
        else:
            out.append(text[i:pos])
            i = pos

    return ''.join(out)


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

    # Strip footnotes and citations (balanced braces; abstracts may nest commands)
    for command in ('footnote', 'footcite', 'cite'):
        raw = strip_command(raw, command)

    # Unescape LaTeX special characters
    raw = raw.replace(r'\&', '&amp;')
    raw = raw.replace(r'\%', '%')
    raw = raw.replace(r'\$', '$')
    raw = raw.replace(r'\#', '#')
    raw = raw.replace(r'\_', '_')

    # Convert common text commands/symbols to HTML
    raw = re.sub(r'\\emph\{([^}]+)\}', r'<em>\1</em>', raw)
    raw = re.sub(r'\\textsc\{([^}]+)\}', r'\1', raw)
    raw = re.sub(r'\\pounds(?![a-zA-Z])', '&pound;', raw)
    raw = re.sub(r'\\textsterling(?![a-zA-Z])', '&pound;', raw)
    raw = re.sub(r'\\textcent(?![a-zA-Z])', '&cent;', raw)
    raw = re.sub(r'\\ldots(?![a-zA-Z])|\\dots(?![a-zA-Z])', '&hellip;', raw)
    raw = re.sub(r'\\[,;:]', ' ', raw)
    raw = raw.replace('~', ' ')

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
    build_id = os.environ.get("BUILD_ID", "")
    build_iso = ""
    if build_id:
        build_iso = datetime.fromtimestamp(int(build_id), tz=timezone.utc).astimezone().isoformat()

    env = Environment(loader=FileSystemLoader(str(SCRIPT_DIR)))
    template = env.get_template("index-template.html.j2")
    html = template.render(
        articles=json.dumps(articles, default=str),
        tags=json.dumps(tags, default=str),
        build_id=build_id,
        build_iso=build_iso
    )
    (SCRIPT_DIR / "index.html").write_text(html)
    print(f"Generated index.html ({len(articles)} articles, {len(tags)} tags)")


if __name__ == '__main__':
    articles, tags = collect_articles()
    generate_index(articles, tags)
