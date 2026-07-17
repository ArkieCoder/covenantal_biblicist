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

build_id = os.environ.get("BUILD_ID", "")
build_iso = ""
if build_id:
    build_iso = datetime.fromtimestamp(int(build_id), tz=timezone.utc).astimezone().isoformat()

env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template(template_name)
print(template.render(
    article_name=article_name,
    article_title=article_title,
    article_description=article_description,
    adobe_client_id=adobe_client_id,
    build_id=build_id,
    build_iso=build_iso
), end="")
