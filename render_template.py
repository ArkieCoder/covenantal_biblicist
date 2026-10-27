#!/usr/bin/env python3
"""Render a Jinja2 article template with the given article name."""

import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import yaml

template_dir = sys.argv[1]
template_name = sys.argv[2]
article_name = sys.argv[3]

# Read metadata if available
article_title = article_name.replace('-', ' ').replace('_', ' ').title()
article_description = ""
metadata_path = Path(template_dir) / "articles" / article_name / "metadata.yaml"
if metadata_path.exists():
    meta = yaml.safe_load(metadata_path.read_text())
    article_title = meta.get("title", article_title)
    article_description = meta.get("description", "")

adobe_client_id = os.environ.get("ADOBE_CLIENT_ID", "bd4cb7ccbcdc4940adb98b75683d410a")
site_url = os.environ.get("SITE_URL", "https://covenantalbiblicist.unitedentropy.com")

build_id = os.environ.get("BUILD_ID", "")
build_iso = ""
if build_id:
    build_iso = datetime.fromtimestamp(int(build_id), tz=timezone.utc).astimezone().isoformat()

# Determine OG image and page path
if article_name and template_name.startswith("article"):
    og_image_path = f"/assets/og/{article_name}.png"
    page_path = f"/articles/{article_name}/"
elif template_name == "about.html.j2":
    og_image_path = "/assets/og/about.png"
    page_path = "/about.html"
elif template_name == "index-template.html.j2" or template_name == "index.html.j2":
    og_image_path = "/assets/og/site.png"
    page_path = "/"
else:
    og_image_path = "/assets/og/site.png"
    page_path = "/"

env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template(template_name)
print(template.render(
    article_name=article_name,
    article_title=article_title,
    article_description=article_description,
    adobe_client_id=adobe_client_id,
    build_id=build_id,
    build_iso=build_iso,
    site_url=site_url,
    og_image_path=og_image_path,
    page_path=page_path
), end="")
