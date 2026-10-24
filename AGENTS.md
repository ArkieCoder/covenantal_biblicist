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
├── base.tex                          # Shared LaTeX preamble (loaded by all articles)
├── set-cropbox.py                    # PDF CropBox setter (Ghostscript + pikepdf)
├── render_template.py                # Jinja2 article template renderer
├── generate_index.py                 # Root index.html generator
├── generate_tags.py                  # Tag index + per-tag page generator
├── article-template.html.j2          # Per-article PDF viewer template
├── index-template.html.j2            # Root index template (search/sort/cards)
├── tag-index-template.html.j2        # Tag listing page template
├── tag-page-template.html.j2         # Per-tag article listing template
├── css/style.css                     # Shared stylesheet
├── js/tagcloud.js                    # Spiral placement tag cloud algorithm
├── js/visitor-count.js               # GoatCounter view count + build ID display
├── articles/
│   └── {article_name}/
│       ├── base.tex                  # Symlink/copy? No — articles use ROOT base.tex via TEXINPUTS
│       ├── main.tex                  # LaTeX source (article-specific content only)
│       ├── metadata.yaml             # Article metadata
│       ├── references.bib            # Bibliography
│       └── index.html                # Generated article viewer page
├── _site/                            # Assembled site for deployment (gitignored)
├── tags/                             # Generated tag pages (committed by CI)
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

**Important**: `build.sh` must be invoked as `./build.sh`, not `bash build.sh`. Python scripts are invoked directly (shebang + chmod +x).

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

### Build Script Internals
- `SCRIPT_DIR` is resolved via `$(cd "$(dirname "$0")" && pwd)`
- `TEXINPUTS="$SCRIPT_DIR:$TEXINPUTS"` — pdflatex finds `base.tex` from the project root (non-recursive)
- All `pdflatex` calls use `-interaction=nonstopmode` — prevents hanging on interactive `?` prompts
- `biber base` is used for all variants (not `biber {name}`) — biber reads from `base.bcf`
- `BUILD_ID` is generated once at the top of `build.sh` via `date +%s` (epoch seconds) and exported for all Python scripts
- Intermediate files (`base.bcf`, `base.out`, `base.aux`, `base.blg`, `base.bbl`, `base.log`, `base.run.xml`) are cleaned after each variant's triple-pass completes
- The script does **not** check biber's exit code, and the cleanup deletes `base.blg` — a biber failure therefore produces PDFs with bold undefined-citation keys and no visible error (see Troubleshooting)

### Embed Version
The embed build compiles with `\def\embedversion{}`:
- `\pagestyle{empty}` suppresses headers/footers
- `\pdfpageheight=16000pt` and `\textheight=15500pt` create tall pages so TeX never breaks mid-section
- `\newpage` before each `\section` starts content on a fresh page
- `set-cropbox.py` uses Ghostscript bbox detection + pikepdf to set per-page CropBox and MediaBox

### Embed LaTeX Internals (`base.tex`)
The embed version uses `\AtBeginDocument` hooks to override TeX's page dimensions:

```latex
\ifdefined\embedversion
  \makeatletter
  \AtBeginDocument{%
    \pdfpageheight=16000pt
    \textheight=15500pt
    \vsize=15500pt
    \global\@colht=\textheight
    \global\@colroom=\textheight
  }
  \makeatother
\fi
```

**Why `\makeatletter`/`\makeatother` is required**: By the time `\AtBeginDocument` tokens are tokenized, earlier packages have executed `\makeatother`, so `@` has catcode 12 (other). Without the wrapper, `\@colht` is tokenized as `\@` (spacefactor command) + `colht` (literal text), producing visible "colht" artifacts in the PDF output. This is the same issue that caused the "opcolopcol" artifact.

**Why `\@colht`/`\@colroom` must be set**: The LaTeX kernel's `\document` macro sets `\@colht`/`\@colroom`/`\vsize` from `\textheight` at line 9637 of `latex.ltx`, *before* `\AtBeginDocument` hooks fire. Without these overrides, `\textheight` would be 15500pt but `\@colht`/`\@colroom` would remain at ~686pt, causing the output routine's `\global \vsize \@colroom` to revert `\vsize` on every page break. TeX's max dimension is 16384pt, so `\pdfpageheight=16000pt` is the practical ceiling.

### CropBox Logic (`set-cropbox.py`)
- `pad = 2` (tight to content bounds)
- `TOP_PAD = 15` — adds 15pt of padding above content on each page
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
    \renewcommand{\small}{\fontsize{12pt}{15pt}\selectfont}%
    \renewcommand{\footnotesize}{\fontsize{11pt}{14pt}\selectfont}%
    \renewcommand{\scriptsize}{\fontsize{9pt}{12pt}\selectfont}%
    \renewcommand{\large}{\fontsize{16pt}{20pt}\selectfont}%
    \renewcommand{\Large}{\fontsize{18pt}{22pt}\selectfont}%
    \normalsize
    \justifying
  }
\fi

\ifdefined\tabletversion
  \AtBeginDocument{%
    \renewcommand{\normalsize}{\fontsize{12pt}{15pt}\selectfont}%
    \renewcommand{\small}{\fontsize{11pt}{14pt}\selectfont}%
    \renewcommand{\footnotesize}{\fontsize{10pt}{13pt}\selectfont}%
    \renewcommand{\scriptsize}{\fontsize{8pt}{11pt}\selectfont}%
    \renewcommand{\large}{\fontsize{14pt}{18pt}\selectfont}%
    \renewcommand{\Large}{\fontsize{16pt}{20pt}\selectfont}%
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
- `adobe_client_id` — from `ADOBE_CLIENT_ID` env var, fallback `bd4cb7ccbcdc4940adb98b75683d410a`
- `build_id` — from `BUILD_ID` env var (epoch seconds)
- `build_iso` — human-readable ISO timestamp derived from `build_id`

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
- GoatCounter analytics script tag in `<head>` (`covenantbiblicist.goatcounter.com`)
- Build ID and Views counters in footer with hover tooltips

### Index Template (`index-template.html.j2`)
- Search input + sort dropdown (date, title, author)
- Expandable article cards with caret toggle
- Abstracts rendered as multi-paragraph HTML with justified text
- "Read ☞" button in flexbox footer aligned with last paragraph
- Client-side filtering and sorting via JavaScript
- GoatCounter analytics script tag in `<head>`

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
- `#footer-bar` — fixed 100px bar on desktop, 50px bar on mobile/tablet (`max-width: 1023px`), flex, vertically centered content
- `.share-email-wrap` — dropdown container for email options
- `.share-email-menu` — popover menu above email icon
- `#adobe-dc-view` — PDF viewer container; `height: calc(100vh - 100px)` on desktop, `min-height: calc(100vh - 50px)` on mobile/tablet to prevent PDF cutoff
- `#footer-icons` — flex row on desktop and mobile/tablet

## Document Structure (LaTeX)

### Section Hierarchy
- `\section{}` for top-level sections (Title Case, unnumbered)
- No `\subsubsection`, `\paragraph`, or `\subparagraph`
- Blank lines precede and follow each `\section` command

### Abstract
- Standard `abstract` environment immediately after `\maketitle`
- Multi-paragraph abstracts are supported and used

### Preamble Organization (`base.tex`)
1. `\documentclass[justified, nobib]{tufte-handout}`
2. Package loading block
3. Custom field formats (QR codes)
4. Custom commands
5. Base geometry override
6. Conditional mobile/tablet font-size blocks
7. Conditional embed page-dimension overrides
8. `\input{main.tex}` (article-specific content starts here)

## Custom Commands

### `\biblever{#1}`
Format Bible verse references in small caps: `\biblever{gen. 1:1}` → `(GEN. 1:1)`

### `\scriptref{#1}`
Right-aligned scriptural attribution (called by `\scripture`, or directly inside footnote text for full-quote Scripture footnotes)

### `\scripture{text}{reference}`
Block scripture quotations with attribution

## Package Usage

| Package | Options | Purpose |
|---------|---------|---------|
| `tufte-handout` | `[justified, nobib]` | Base document class |
| `verse` | - | Poetry/verse typesetting |
| `gmverse` | - | Extended verse formatting |
| `alltt` | - | Verbatim-like environments |
| `marginfix` | - | Margin note spacing fixes (unconditional) |
| `biblatex` | `[style=verbose]` | Bibliography management |
| `qrcode` | - | QR code generation |
| `fontsize` | `[fontsize=9pt]` | Base font size override |

## Citation/Bibliography Style

- **Engine**: biber (not bibtex)
- **Style**: `biblatex` with `style=verbose`
- **Citation Command**: `\footcite{key}`
- **Resource File**: `references.bib`
- **Scripture citations**: full quotations live in footnotes as the NASB verse text followed by `\scriptref{Ref \biblever{nasb}}`; bare verse references are `\footnote{Ref \biblever{nasb}}`; the label is uniformly `(NASB)` (1995 text)
- URLs render as QR codes via custom `\DeclareFieldFormat{url}`

**Known warning**: `Package biblatex Warning: Patching footnotes failed.` — This is expected and harmless. `tufte-handout` renders footnotes via `\marginpar` rather than the standard `\@footnotetext`, so `biblatex`'s footnote detection patch cannot hook in. Citations still render correctly in the margin.

## Typography Conventions

- **Base size**: 9pt (via `fontsize` package)
- **Line spread**: `\linespread{1.25}`
- **`\textit{}`**: Primary emphasis (used extensively)
- **`\textsc{}`**: Used in `\biblever` for verse references
- **Bold/Underline**: Never used

## CI/CD (`.github/workflows/`)

### `deploy.yml`
- Triggers on push to `master`
- Runs in `texlive/texlive:latest` Docker container (has pdflatex, biber, Ghostscript, Python)
- `ADOBE_CLIENT_ID` injected from GitHub secret
- Python deps installed via `pip3 install --break-system-packages -r requirements.txt`
- Builds all articles, runs Pagefind for search indexing
- Commits built artifacts (PDFs, HTML, tags/) back to repo with `[skip ci]`
- Uses `git pull --rebase origin master` before push to handle concurrent changes
- `git config --global --add safe.directory` required (Docker checkout owned by root, CI runs as UID 1001)
- `actions/configure-pages@v5` runs AFTER the commit step (running it before breaks git credential helpers)
- Deploys to GitHub Pages via `actions/upload-pages-artifact` from `_site/`

### `pr-check.yml`
- Triggers on PRs to `master` with `types: [opened, synchronize, reopened]` (without explicit types, GitHub also triggers on push events associated with merged PRs, causing spurious 0s-duration failures)
- Uses `dorny/paths-filter` to detect changed articles
- Matrix builds only changed articles (or all if shared files changed)
- Runs Pagefind for search indexing

## Content Patterns

### Argumentative Essay Structure
1. Context/Background → 2. Data → 3. Problem → 4. Solution

### Theological Vocabulary
- "covenant order", "sphere sovereignty", "complementarianism", "shepherd" (as verb)

## Troubleshooting

### Biber aborts mid-run (citations render as bold citekeys)
**Symptom**: Every citation in the PDF renders as its raw bold citekey (e.g., **sowellblack**). This is what biblatex does whenever an entry is missing from the `.bbl` — the `.bbl` is empty, absent, or unreadable. If it affects *every* article in a build — including articles with valid citekeys and unmodified sources — the cause is biber itself, not the LaTeX or any `.bib` file. (CI building the same sources hydrated in Docker confirms the problem is local.)

**Root cause**: Biber is a PAR-packed Perl application that extracts its modules to a cache directory. macOS periodically prunes `/var/folders` temp directories by mtime, deleting extracted modules; PAR then partially re-extracts, leaving a mixed cache that dies the first time biber requires an eaten module. Observed signature (2026-10): **exit code 25, no error message anywhere**, and a `.blg` that stops dead after `Found BibTeX data source '<file>'` — no `ERROR` line, no `Processing entry`, no `Writing 'base.bbl'`, no `EXIT`. Biber dies in the entry-mapping/decode phase. PAR ships a `_CANARY_.txt` file in the cache precisely to detect this macOS cleanup. An earlier variant of the same failure produced a 0-byte `.bbl` with `Unicode::UCD: failed to find unicore/version` in `--debug` mode.

**Fix**: Delete the whole PAR directory so biber performs one complete fresh extraction:
```bash
rm -rf "$(biber --cache)"        # prints the exact cache path
rm -rf /var/folders/*/*/T/par-*  # or the whole per-user PAR dir
```
The real path has **two directory levels before `/T/`** (`/var/folders/<x>/<random>/T/par-<uid>/cache-<hash>`); the old single-level glob `/var/folders/*/T/par-*` matches nothing and silently fails. Re-run the build; biber regenerates the cache on next invocation. If it still exits 25 after a full purge, reinstall the binary: `tlmgr install --reinstall biber`.

**Diagnostics**:
- A nonexistent citekey does *not* break biber or the cache — biber logs `Citekey 'x' not found ... - skipping`, writes the `.bbl` without it, and the citation renders bold because it is genuinely undefined. Fix the typo and rebuild; no cache purge needed.
- On TeX Live 2026, `tlmgr status` was removed; use `tlmgr info <pkg>` for package details.
- `build.sh` ignores biber's exit code and deletes `base.blg` in its cleanup, so biber failures leave no trace. To see the error, run the pipeline by hand:
  ```bash
  cd articles/<name>
  TEXINPUTS="$(cd ../.. && pwd):" pdflatex -interaction=nonstopmode base.tex
  biber base    # then inspect base.blg; `echo $?` gives the exit code
  ```
- To check a built PDF for citation hydration without opening it:
  ```bash
  pdftotext articles/<name>/<name>.pdf - | grep '<citekey>'
  ```
  Raw citekey present = unresolved; rendered author/title instead = hydrated.

### "opcolopcol" or "colht" artifacts in PDF output
These appear when `\makeatletter`/`\makeatother` is not wrapping `\AtBeginDocument` hooks that use `@` in LaTeX internal commands (e.g., `\@colht`, `\@opcol`). Without the wrapper, `@` has catcode 12 (other) when the tokens are created, causing commands like `\@colht` to be split into `\@` (spacefactor) + literal `colht`.

### `\vsize` reverts to small value in embed builds
If embed pages break mid-section, check that `\global\@colht=\textheight` and `\global\@colroom=\textheight` are set in the `\AtBeginDocument` hook. The LaTeX kernel sets these from `\textheight` before hooks fire, and the output routine uses `\@colroom` to reset `\vsize` on every page break.

## Proofreading

No spellchecker is installed — proofread by reading the entire file (see the long-line tip below) plus targeted greps:

```bash
grep -n -o -E '\b([A-Za-z]+) \1\b' main.tex   # doubled words
grep -n -o -E '\b[A-Z]{2}[a-z]+' main.tex     # case slips like "CHristians"
grep -n -E 'teh |adn |recieve|seperate|occured|definately|maintan|commited|shoul [a-z]| dbe\b' main.tex
```

Recurring catches (2026-10): `maintanence`, `CHristians`, split words (`shoul dbe`), title casing (`Christianity And Liberalism`), missing hyphens in attributive compounds (`self serving`, `right wing`). Block quotations (Hansard, Belczak, etc.) are verbatim: when wording or punctuation looks off, verify against the source rather than editing the quote — including em-dash spacing, which is often a transcription artifact.

## Notes for Editing

- Documents are **drafts** — "The Problem" and "The Solution" sections may be skeletal
- `\scripture` is defined but not yet used; `\biblever` is in use (once in `reach_men_reach_families`, 13 times in `reflections_on_capital_punishment`, and called directly by footnotes rather than through `\scripture`)
- `verse`, `gmverse`, and `alltt` packages are loaded but may be unused
- QR code feature is set up but may be unused (no URLs in bibliography yet)
- `main.tex` paragraphs are one-per-line and can exceed the reader's 2,000-character line limit — read long lines in full with `sed -n 'Np' main.tex | fold -s -w 118`
- When changing `article-template.html.j2`, you must rebuild all articles (`./build.sh`) so that each article's `index.html` is regenerated from the template — just changing the template does not update existing article pages
- Social share buttons were removed in favor of direct URL sharing; Facebook's "User opted out of platform" restrictions make SDK/share buttons unreliable
- `_site/` is gitignored — generated output
- `tags/` is committed by CI (removed from `.gitignore`)
- `TASKS.md` is untracked — implementation task tracking
