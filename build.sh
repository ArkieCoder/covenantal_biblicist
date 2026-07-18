#!/bin/bash

# Build script for Covenantal Biblicist articles
# Usage: ./build.sh [article_dir]
#   No args: build all articles under articles/
#   With arg: build the specified article directory (e.g., reach_men_reach_families)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARTICLES_DIR="$SCRIPT_DIR/articles"
SITE_DIR="$SCRIPT_DIR/_site"
TEMPLATE_DIR="$SCRIPT_DIR"
TEMPLATE="article-template.html.j2"
RENDER="$SCRIPT_DIR/render_template.py"
CROPCBOX="$SCRIPT_DIR/set-cropbox.py"

# Unified build ID (epoch seconds) for all pages
BUILD_ID="$(date +%s)"
export BUILD_ID

build_article() {
  local dir="$1"
  local name="$(basename "$dir")"

  echo "=== Building: $name ==="

  (
    cd "$dir" || exit 1

    # Generate article index.html from Jinja2 template
    "$RENDER" "$TEMPLATE_DIR" "$TEMPLATE" "$name" > index.html

    export TEXINPUTS="$SCRIPT_DIR:$TEXINPUTS"

    # Canonical version (full tufte layout)
    pdflatex base.tex
    biber base
    pdflatex base.tex
    pdflatex base.tex
    rm -vf base.bcf base.out base.aux base.blg base.bbl base.log base.run.xml
    mv base.pdf "$name.pdf"

    # Embed version (no headers, newpage at sections, variable page heights via CropBox)
    pdflatex "\def\embedversion{} \input base.tex"
    biber base
    pdflatex "\def\embedversion{} \input base.tex"
    pdflatex "\def\embedversion{} \input base.tex"

    # Set CropBox per page: tight to content bounds (preserves annotations)
    "$CROPCBOX" base.pdf "$name-embed.pdf"

    # Tablet variant (embed layout + larger font)
    pdflatex "\def\embedversion{} \def\tabletversion{} \input base.tex"
    biber base
    pdflatex "\def\embedversion{} \def\tabletversion{} \input base.tex"
    pdflatex "\def\embedversion{} \def\tabletversion{} \input base.tex"
    "$CROPCBOX" base.pdf "$name-embedtablet.pdf"

    # Mobile variant (embed layout + largest font)
    pdflatex "\def\embedversion{} \def\mobileversion{} \input base.tex"
    biber base
    pdflatex "\def\embedversion{} \def\mobileversion{} \input base.tex"
    pdflatex "\def\embedversion{} \def\mobileversion{} \input base.tex"
    "$CROPCBOX" base.pdf "$name-embedmobile.pdf"

    rm -vf base.pdf base.bcf base.out base.aux base.blg base.bbl base.log base.run.xml
  )

  echo "=== Done: $name ==="
}

assemble_site() {
  echo "=== Assembling site ==="
  rm -rf "$SITE_DIR"
  mkdir -p "$SITE_DIR/articles"
  mkdir -p "$SITE_DIR/tags"
  mkdir -p "$SITE_DIR/css"
  mkdir -p "$SITE_DIR/js"

  # Copy shared CSS
  cp "$SCRIPT_DIR/css/style.css" "$SITE_DIR/css/"

  # Copy JS
  cp "$SCRIPT_DIR/js/tagcloud.js" "$SITE_DIR/js/"
  cp "$SCRIPT_DIR/js/visitor-count.js" "$SITE_DIR/js/"

  # Copy root index
  cp "$SCRIPT_DIR/index.html" "$SITE_DIR/"

  # Copy article artifacts
  for dir in "$ARTICLES_DIR"/*/; do
    local name="$(basename "$dir")"
    if [ -f "$dir/index.html" ]; then
      mkdir -p "$SITE_DIR/articles/$name"
      cp "$dir/index.html" "$SITE_DIR/articles/$name/"
      cp "$dir"/*.pdf "$SITE_DIR/articles/$name/" 2>/dev/null || true
    fi
  done

  # Copy tag pages
  if [ -d "$SCRIPT_DIR/tags" ]; then
    cp -r "$SCRIPT_DIR/tags/"* "$SITE_DIR/tags/" 2>/dev/null || true
  fi

  echo "=== Site assembled ==="
}

# Build articles
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

# Generate index and tag pages
python3 "$SCRIPT_DIR/generate_index.py"
python3 "$SCRIPT_DIR/generate_tags.py"

# Assemble site for deployment
assemble_site
