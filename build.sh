#!/bin/bash

# Build script for Covenantal Biblicist articles
# Usage: ./build.sh [article_dir]
#   No args: build all articles under articles/
#   With arg: build the specified article directory (e.g., reach_men_reach_families)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARTICLES_DIR="$SCRIPT_DIR/articles"
TEMPLATE_DIR="$SCRIPT_DIR"
TEMPLATE="article-template.html.j2"
RENDER="$SCRIPT_DIR/render_template.py"
CROPCBOX="$SCRIPT_DIR/set-cropbox.py"

build_article() {
  local dir="$1"
  local name="$(basename "$dir")"

  echo "=== Building: $name ==="

  (
    cd "$dir" || exit 1

    # Generate article index.html from Jinja2 template
    "$RENDER" "$TEMPLATE_DIR" "$TEMPLATE" "$name" > index.html

    # Canonical version (full tufte layout)
    pdflatex main.tex
    biber main
    pdflatex main.tex
    pdflatex main.tex
    rm -vf main.bcf main.out main.aux main.blg main.bbl main.log main.run.xml
    mv main.pdf "$name.pdf"

    # Embed version (no headers, newpage at sections, variable page heights via CropBox)
    pdflatex "\def\embedversion{} \input main.tex"
    biber main
    pdflatex "\def\embedversion{} \input main.tex"
    pdflatex "\def\embedversion{} \input main.tex"

    # Set CropBox per page: tight to content bounds (preserves annotations)
    "$CROPCBOX" main.pdf "$name-embed.pdf"

    # Tablet variant
    pdflatex "\def\tabletversion{} \input main.tex"
    biber main
    pdflatex "\def\tabletversion{} \input main.tex"
    pdflatex "\def\tabletversion{} \input main.tex"
    "$CROPCBOX" main.pdf "$name-tablet.pdf"

    # Mobile variant
    pdflatex "\def\mobileversion{} \input main.tex"
    biber main
    pdflatex "\def\mobileversion{} \input main.tex"
    pdflatex "\def\mobileversion{} \input main.tex"
    "$CROPCBOX" main.pdf "$name-mobile.pdf"

    rm -vf main.pdf main.bcf main.out main.aux main.blg main.bbl main.log main.run.xml
  )

  echo "=== Done: $name ==="
}

if [ -n "$1" ]; then
  if [ -f "$ARTICLES_DIR/$1/main.tex" ]; then
    build_article "$ARTICLES_DIR/$1"
  else
    echo "Error: articles/$1/main.tex not found" >&2
    exit 1
  fi
else
  found=0
  for dir in "$ARTICLES_DIR"/*/; do
    if [ -f "$dir/main.tex" ]; then
      build_article "$dir"
      found=1
    fi
  done
  if [ "$found" -eq 0 ]; then
    echo "No articles found" >&2
    exit 1
  fi
fi
