#!/usr/bin/env python3
"""Render a Jinja2 article template with the given article name."""

import sys
from jinja2 import Environment, FileSystemLoader

template_dir = sys.argv[1]
template_name = sys.argv[2]
article_name = sys.argv[3]

env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template(template_name)
print(template.render(article_name=article_name), end="")
