#!/usr/bin/env python3
"""Generate tag index and per-tag pages from article metadata."""

import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

SCRIPT_DIR = Path(__file__).parent
ARTICLES_DIR = SCRIPT_DIR / "articles"
TAGS_DIR = SCRIPT_DIR / "tags"


def collect_tags():
    """Collect all tags and their articles."""
    tags = {}
    for article_dir in sorted(ARTICLES_DIR.iterdir()):
        if not article_dir.is_dir():
            continue

        metadata_path = article_dir / "metadata.yaml"
        if not metadata_path.exists():
            continue

        meta = yaml.safe_load(metadata_path.read_text())
        if meta.get('status') != 'published':
            continue

        article_info = {
            'title': meta['title'],
            'author': meta['author'],
            'date': meta['date'],
            'description': meta['description'],
            'url': f"../../articles/{article_dir.name}/index.html"
        }

        for tag in meta.get('tags', []):
            if tag not in tags:
                tags[tag] = []
            tags[tag].append(article_info)

    # Sort articles within each tag by date descending
    for tag in tags:
        tags[tag].sort(key=lambda a: a['date'], reverse=True)

    return tags


def generate_tag_pages(tags):
    """Generate tag index and per-tag pages."""
    env = Environment(loader=FileSystemLoader(str(SCRIPT_DIR)))

    # Generate tag index
    tag_index_template = env.get_template("tag-index-template.html.j2")
    tag_names = sorted(tags.keys())
    html = tag_index_template.render(
        tags=[{'name': t, 'count': len(tags[t])} for t in tag_names]
    )
    TAGS_DIR.mkdir(exist_ok=True)
    (TAGS_DIR / "index.html").write_text(html)
    print(f"Generated tags/index.html ({len(tag_names)} tags)")

    # Generate per-tag pages
    tag_page_template = env.get_template("tag-page-template.html.j2")
    for tag_name in tag_names:
        tag_dir = TAGS_DIR / tag_name.replace(' ', '-').lower()
        tag_dir.mkdir(exist_ok=True)
        html = tag_page_template.render(
            tag=tag_name,
            articles=tags[tag_name]
        )
        (tag_dir / "index.html").write_text(html)
        print(f"Generated tags/{tag_dir.name}/index.html ({len(tags[tag_name])} articles)")


if __name__ == '__main__':
    tags = collect_tags()
    generate_tag_pages(tags)
