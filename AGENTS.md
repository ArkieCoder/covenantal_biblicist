# AGENTS.md - LaTeX Blog Project Conventions

## Project Overview

- **Type**: Multi-article blog using LaTeX (`tufte-handout` class) + Adobe PDF Embed API
- **Purpose**: Theological papers on complementarian ministry and church governance
- **Build System**: pdflatex + biber + Python generators via `build.sh`
- **Output**: 4 PDF variants per article + generated index/tags + assembled site in `_site/`
- **Web Viewer**: Jinja2 templates with Adobe PDF Embed API, Font Awesome icons
- **Deployment**: GitHub Pages via GitHub Actions

## Repository Structure

```
├── build.sh                          # Main build script
├── set-cropbox.py                    # PDF CropBox setter (Ghostscript + pikepdf)
├── render_template.py                # Jinja2 article template renderer
├── generate_index.py                 # Root index.html generator
├── generate_tags.py                  # Tag index + per-tag page generator
├── article-template.html.j2          # Per-article PDF viewer template
├── index-template.html.j2            # Root index template (search/sort/cards)
├── tag-index-template.html.j2        # Tag listing page template
├── tag-page-template.html.j2         # Per-tag article listing template
├── css/style.css                     # Shared stylesheet
├── articles/
│   └── {article_name}/
│       ├── main.tex                  # LaTeX source
│       ├── metadata.yaml             # Article metadata
│       ├── references.bib            # Bibliography
│       └── index.html                # Generated article viewer page
├── _site/                            # Assembled site for deployment (gitignored)
├── tags/                             # Generated tag pages (gitignored)
├── .github/workflows/
│   ├── deploy.yml                    # Deploy to GitHub Pages on push to master
│   └── pr-check.yml                  # Matrix build on PRs
├── .gitignore
└── TASKS.md                          # Implementation task list (untracked)
```

## Build System

### Pipeline (`build.sh`)
```bash
./build.sh                    # Build all articles + generate index/tags + assemble site
./build.sh {article_name}     # Build single article
```

Per article, `build.sh` produces 4 PDF variants:
1. **Desktop** (`{name}.pdf`): `pdflatex base.tex` — canonical tufte layout
2. **Embed** (`{name}-embed.pdf`): `\def\embedversion{}` — no headers, `\newpage` before sections, CropBox+MediaBox applied
3. **Embed Tablet** (`{name}-embedtablet.pdf`): `\def\embedversion{} \def\tabletversion{}` — embed layout + 12pt font, CropBox+MediaBox applied
4. **Embed Mobile** (`{name}-embedmobile.pdf`): `\def\embedversion{} \def\mobileversion{}` — embed layout + 14pt font, CropBox+MediaBox applied

Each variant gets its own pdflatex triple-pass + biber cycle.

After article builds, `build.sh` runs:
- `generate_index.py` → `index.html`
- `generate_tags.py` → `tags/index.html` + `tags/{tag}/index.html`
- `assemble_site()` → copies everything into `_site/`

### Embed Version
The embed build compiles with `\def\embedversion{}`:
- `\pagestyle{empty}` suppresses headers/footers
- `\pdfpageheight=16000pt` and `\textheight=15500pt` create tall pages so TeX never breaks mid-section
- `\newpage` before each `\section` starts content on a fresh page
- `set-cropbox.py` uses Ghostscript bbox detection + pikepdf to set per-page CropBox and MediaBox

### CropBox Logic (`set-cropbox.py`)
- `pad = 2` (tight to content bounds)
- `MIN_HEIGHT = 200` — pages with content < 200pt get expanded CropBox anchored at content top
- This prevents the Adobe PDF viewer from clipping sparse pages (e.g., last page with short section)
- Pages with content ≥ 200pt get tight cropping
- **MediaBox is resized to match CropBox** — eliminates whitespace gaps in the Adobe PDF Embed viewer

### Responsive LaTeX Geometry
Conditional font-size redefinitions in `base.tex` (after base `\geometry{}`, before `\input{main.tex}`):
```latex
\ifdefined\mobileversion
  \AtBeginDocument{%
    \renewcommand{\normalsize}{\fontsize{14pt}{18pt}\selectfont}%
    \normalsize
    \justifying
  }
\fi

\ifdefined\tabletversion
  \AtBeginDocument{%
    \renewcommand{\normalsize}{\fontsize{12pt}{15pt}\selectfont}%
    \normalsize
    \justifying
  }
\fi
```
Mobile/tablet variants share the same geometry as desktop (`base.tex` default `\geometry{}`). `marginfix` is loaded unconditionally for all variants (prevents margin note collisions).

### Dependencies
- TeX distribution (TeX Live/MacTeX): `pdflatex`, `biber`, `tufte-handout`, all packages
- Python 3: `pikepdf`, `jinja2`, `pyyaml`
- `ghostscript` (for bounding box detection)
- `pikepdf` (for CropBox manipulation)

## Article Metadata (`metadata.yaml`)
```yaml
title: "Article Title"
author: "Author Name"
date: 2026-07-16
status: published          # published | draft (drafts excluded from index/tags)
tags:
  - tag-name
description: "One-line description."
```

## Template System

### `render_template.py`
Renders Jinja2 article template. Reads `metadata.yaml` and passes:
- `article_name` — directory name (e.g., `reach_men_reach_families`)
- `article_title` — from metadata (e.g., "Reach Men, Reach Families")
- `article_description` — from metadata

### Article Template (`article-template.html.j2`)
- Loads shared CSS from `../../css/style.css`
- Loads Font Awesome 6.5.1 from CDN
- Header: "Covenantal Biblicist" linking to `../../` (root index)
- Adobe PDF Embed API with responsive variant selection:
  - `<600px` → embedmobile variant
  - `600-1023px` → embedtablet variant
  - `≥1023px` → embed variant
- Footer bar (`#footer-bar`): 100px fixed bar with gradient
  - Left: "Covenantal Biblicist" title (links to index, appears on scroll)
  - Right: Icon row — Print (opens PDF), Email (dropdown: mailto + Gmail), Facebook, X
- Share URLs use browser-native: `mailto:`, Gmail compose URL, Facebook share, X intent
- Email icon has dropdown with "Mail client" (native) and "Gmail" options

### Index Template (`index-template.html.j2`)
- Search input + sort dropdown (date, title, author)
- Expandable article cards with caret toggle
- Abstracts rendered as multi-paragraph HTML with justified text
- "Read ☞" button in flexbox footer aligned with last paragraph
- Client-side filtering and sorting via JavaScript

### Tag Templates
- `tag-index-template.html.j2` — lists all tags with article counts
- `tag-page-template.html.j2` — per-tag article listing with back link

## CSS Conventions (`css/style.css`)

### Color Variables
```css
--gunmetal: #2c3539;
--link-color: #1a1a2e;
--meta-color: #666;
--text-color: #333;
--muted-color: #555;
--border-color: #ddd;
--light-border: #eee;
```

### Key Patterns
- `.abstract p` — justified text, paragraph spacing
- `.abstract-footer` — flexbox for last paragraph + "Read ☞" button
- `.read-more` — small-caps, bordered box, inline-flex with finger icon (U+261E)
- `#footer-bar` — fixed 100px bar, flex, vertically centered content
- `.share-email-wrap` — dropdown container for email options
- `.share-email-menu` — popover menu above email icon

## Document Structure (LaTeX)

### Section Hierarchy
- `\section{}` for top-level sections (Title Case, unnumbered)
- No `\subsubsection`, `\paragraph`, or `\subparagraph`
- Blank lines precede and follow each `\section` command

### Abstract
- Standard `abstract` environment immediately after `\maketitle`
- Multi-paragraph abstracts are supported and used

### Preamble Organization
1. `\documentclass[justified, nobib]{tufte-handout}`
2. Package loading block
3. Custom field formats (QR codes)
4. Custom commands
5. Base geometry override
6. Conditional mobile/tablet font-size blocks
7. Title metadata

## Custom Commands

### `\biblever{#1}`
Format Bible verse references in small caps: `\biblever{gen. 1:1}` → `(GEN. 1:1)`

### `\scriptref{#1}`
Right-aligned scriptural attribution (called by `\scripture`)

### `\scripture{text}{reference}`
Block scripture quotations with attribution

## Package Usage

| Package | Options | Purpose |
|---------|---------|---------|
| `tufte-handout` | `[justified, nobib]` | Base document class |
| `verse` | - | Poetry/verse typesetting |
| `gmverse` | - | Extended verse formatting |
| `alltt` | - | Verbatim-like environments |
| `marginfix` | - | Margin note spacing fixes |
| `biblatex` | `[style=verbose]` | Bibliography management |
| `qrcode` | - | QR code generation |
| `fontsize` | `[fontsize=9pt]` | Base font size override |

## Citation/Bibliography Style

- **Engine**: biber (not bibtex)
- **Style**: `biblatex` with `style=verbose`
- **Citation Command**: `\footcite{key}`
- **Resource File**: `references.bib`
- URLs render as QR codes via custom `\DeclareFieldFormat{url}`

## Typography Conventions

- **Base size**: 9pt (via `fontsize` package)
- **Line spread**: `\linespread{1.25}`
- **`\textit{}`**: Primary emphasis (used extensively)
- **`\textsc{}`**: Used in `\biblever` for verse references
- **Bold/Underline**: Never used

## CI/CD (`.github/workflows/`)

### `pr-check.yml`
- Triggers on PRs to `master`
- Uses `dorny/paths-filter` to detect changed articles
- Matrix builds only changed articles (or all if shared files changed)
- Runs Pagefind for search indexing

### `deploy.yml`
- Triggers on push to `master`
- Builds all articles, assembles site, deploys to GitHub Pages

## Content Patterns

### Argumentative Essay Structure
1. Context/Background → 2. Data → 3. Problem → 4. Solution

### Theological Vocabulary
- "covenant order", "sphere sovereignty", "complementarianism", "shepherd" (as verb)

## Notes for Editing

- Documents are **drafts** — "The Problem" and "The Solution" sections may be skeletal
- `\biblever` and `\scripture` commands are defined but may not yet be used
- `verse`, `gmverse`, and `alltt` packages are loaded but may be unused
- QR code feature is set up but may be unused (no URLs in bibliography yet)
- `_site/` and `tags/` are gitignored — generated output
- `TASKS.md` is untracked — implementation task tracking
