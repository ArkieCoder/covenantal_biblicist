#!/bin/bash
# Build script for Covenantal Biblicist articles
# Usage: ./build.sh [article_dir]
#   No args: build all articles under articles/
#   With arg: build the specified article directory

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARTICLES_DIR="$SCRIPT_DIR/articles"
SITE_DIR="$SCRIPT_DIR/_site"
CROPCBOX="$SCRIPT_DIR/set-cropbox.py"
RENDER="$SCRIPT_DIR/render_template.py"
TEMPLATE_DIR="$SCRIPT_DIR"
TEMPLATE="article-template.html.j2"

build_article() {
  local dir="$1"
  local name="$(basename "$dir")"

  echo "=== Building: $name ==="

  (
    cd "$dir" || exit 1

    # Generate article index.html
    "$RENDER" "$TEMPLATE_DIR" "$TEMPLATE" "$name" > index.html

    # Desktop variant (canonical)
    pdflatex main.tex
    biber main
    pdflatex main.tex
    pdflatex main.tex
    mv main.pdf "$name.pdf"
    "$CROPCBOX" "$name.pdf" "$name-embed.pdf"

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

    # Cleanup
    rm -vf main.pdf main.bcf main.out main.aux main.blg main.bbl main.log main.run.xml
  )

  echo "=== Done: $name ==="
}

assemble_site() {
  echo "=== Assembling site ==="
  rm -rf "$SITE_DIR"
  mkdir -p "$SITE_DIR/articles"
  mkdir -p "$SITE_DIR/tags"
  mkdir -p "$SITE_DIR/css"

  # Copy shared CSS
  cp "$SCRIPT_DIR/css/style.css" "$SITE_DIR/css/"

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
