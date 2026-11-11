# AGENTS.md - LaTeX Blog Project Conventions

## Project Overview

- **Type**: Multi-article blog using LaTeX (`tufte-handout` class) + Adobe PDF Embed API
- **Purpose**: Theological papers on complementarian ministry and church governance
- **Build System**: pdflatex + biber + Python generators via `build.sh`
- **Output**: 4 PDF variants per article + generated index/tags + assembled site in `_site/`
- **Web Viewer**: Jinja2 templates with Adobe PDF Embed API, Font Awesome icons
- **Deployment**: GitHub Pages via GitHub Actions

## Content Policy

- **ALL ARTICLE CONTENT IS HUMAN-CREATED**: Never use AI tools to generate, rewrite, or substantively edit the content of articles in `articles/*/main.tex`. All theological arguments, ideas, and prose must remain entirely human-authored. AI assistance is only permitted for technical/build infrastructure, formatting fixes, and documentation - never for article substance.

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
- `EXTRA_WHITESPACE_LAST_PAGE = 200` — after cropping, adds configurable extra whitespace to the bottom of the last page (extends CropBox/MediaBox downward) to prevent clipping in the Adobe PDF Embed viewer
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
- Python 3: `pikepdf`, `jinja2`, `pyyaml`, `Pillow`
- `ghostscript` (for bounding box detection)
- CI (`texlive/texlive:latest` / Debian) installs Python deps via OS packages: `python3-pil`, `python3-yaml`, `python3-jinja2`, `python3-pikepdf` (avoids pip/source-build issues across changing Python versions)

## Open Graph Preview Images

### Overview
- **Generator**: `generate_og_images.py` creates 1200×630 PNG previews for social sharing
- **Output**: `assets/og/{article_name}.png` for published articles, plus `site.png` and `about.png`
- **Facebook cover**: `assets/fb/cover-1702x630.png` (2×) and `cover-851x315.png`, generated by the same script from the site/about card design
- **Facebook profile picture**: `assets/fb/profile-1024x1024.png`, generated by `generate_profile_pic()`
- **Build integration**: `build.sh` runs the generator early and copies `assets/` to `_site/`

### Design
- **Background**: `#2c3539` (gunmetal)
- **Blog title** ("COVENANTAL BIBLICIST"): Copperplate, white, uppercased, centered horizontally
- **Separator**: Sans-serif tilde `~` (Helvetica) with generous vertical spacing
- **Article title**: Palatino Italic (matches tufte/psnfss), white, centered, auto-wrapped, italic. Font size auto-shrinks for long titles (max 4 lines)
- **Border**: Double white border (outer 1px at inset 2px, inner 1px at inset 8px with 6px gap) with L-shaped corner flourishes (arms at inset 16px, 22px long)
- **Site/About pages**: Blog title centered vertically with no separator

### Facebook Page cover
- **Sizes**: 851×315 is Meta's recommended size; 1702×630 is the 2× render (Facebook downscales cleanly, and it stays crisp on high-DPI screens)
- **Wordmark span**: `FB_WORDMARK_SPAN = 0.75` of the canvas width. This is a hard constraint, not a taste choice: mobile crops the cover to ~2.4:1 **left-aligned** (only the left ~756 of 851 px survive), and the profile picture overlaps the left ~40px. At 0.87 (the OG card ratio) the tail of "BIBLICIST" is clipped on phones
- **Border/flourish metrics** scale with canvas width via `add_border_and_ornaments(img, scale=width/WIDTH)`, so the cover is proportionally identical to the OG cards
- **Edge margin and title lift**: `FB_COVER_MARGIN = 5` px and `FB_COVER_TITLE_LIFT = 20` px, both in 1× (851×315) pixels and doubled on the 1702×630 render via `FB_COVER_REF_WIDTH`. The margin is passed as `inset`, which overrides the outer rule's position and shifts the inner rule and corner flourishes inward with it, so every gap in the assembly is preserved (outer 5/inner 10 at 1×, outer 10/inner 18 at 2×). The lift raises the wordmark above the vertical centre
- **Wordmark baseline**: `generate_wordmark_card()` centres on the ink *height* and ignores the font's `bbox[1]` top offset, so the wordmark sits ~9 px (1×) below true centre before the lift is applied. Fixing that would move it a further 9 px up, on top of the requested 20 px
- **No tilde, no article title**: same layout as `site.png` / `about.png`
- **Assets ship with the site**: `assets/` is copied wholesale into `_site/`, so the covers are reachable at `/assets/fb/` for uploading to Facebook

### Facebook profile picture
- **Output**: `assets/fb/profile-1024x1024.png` (square; Facebook applies the circular crop itself, so no mask or ring is baked in)
- **Mark**: Copperplate **Bold** (index 2) `C` and `B` flanking a dagger cross, `#f5f5f5` on the `#2c3539` ground
- **Constants**: `PROFILE_CAP = 315`, `PROFILE_GAP = 108`, `PROFILE_PINCH = 0.30`, `PROFILE_LETTER_STRETCH = 2.4`, `PROFILE_CROSS_HEIGHT = 560`, rendered at `PROFILE_SUPERSAMPLE = 2` and downscaled once
- **Pinch**: each letter is compressed toward its *inner* edge by `k = 1 - strength·t²` (t = -1..1 down the ink) — a second-order match to the crop circle, so the outer corners tuck inside it. Stretch is applied *before* pinch so the taper is computed against the stretched height. The C is pinched on the left, the B on the right
- **Vertical stretch**: Copperplate Bold is 1.35× as wide as its cap height, so a C and B side by side read squat. The letters are stretched on the **vertical axis only** (width pinned at 880 px, vertical stems stay 92 px) to 758 px tall — 74 % of the canvas against 86 % wide. Horizontal strokes (the C's arms, the B's bowl tops) thicken in proportion; that is the accepted cost of the stretch
- **Cross**: the Copperplate dagger `†` (U+2020) — the only cross-like glyph in the font (`✝` U+271D, `✠` U+2720, `✙` U+2719 all fall back to `.notdef`). Lengthened to 560 px by splitting the glyph at the guard and stretching **only the stem segments above and below** it. Scaling the glyph normally would take the guard from 73 px to 153 px while the stem stayed thin, inverting the weight; band-splitting keeps the guard at 73 px with its flared ends intact and leaves the crossguard 29 % from the top
- **Fits the crop**: ink 880 × 758 px, max radius 468 of 512, i.e. 44 px clearance inside the circle. Width is the binding constraint (two Copperplate letters plus a cross cannot exceed ~880 px in a 1024 px circle without the outer corners clipping), so a taller mark needs a narrower gap, not more stretch
- **Why drawn crosses were rejected**: a plain rectangle cross (independent height/bar/stroke) reads as a plus sign and loses the dagger's flared, notched bar ends

### Implementation
- **Fonts**: Bundled in `fonts/` for reproducibility (Copperplate.ttc, Palatino.ttc, cmunti.otf, cmunrm.otf, lmroman*.otf). Copied from system/TeX Live.
- **Templates**: All templates include OG and Twitter Card meta tags. `render_template.py` passes `site_url`, `og_image_path`, and `page_path` from environment.
- **Environment**: `SITE_URL` defaults to `https://covenantalbiblicist.unitedentropy.com` (set in CI via `deploy.yml`)
- **CI**: `generate_og_images.py` uses Pillow via the OS `python3-pil` package in CI (no pip source build)

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
- Justified HTML text (`#content p`, `#content li`, `.abstract p`, `.abstract-footer p`) uses `hyphens: auto` + `-webkit-hyphens: auto`, `overflow-wrap: break-word`, and `hyphenate-limit-chars: 6 3 3` to reduce awkward spacing/rivers; requires `<html lang="en">` (already set in templates).
- `.abstract p` — justified text, paragraph spacing
- `.abstract-footer` — flexbox for last paragraph + "Read ☞" button
- `.read-more` — small-caps, bordered box, inline-flex with finger icon (U+261E)
- `#footer-bar` — fixed 100px bar on desktop, 50px bar on mobile/tablet (`max-width: 1023px`), flex, vertically centered content
- `.share-email-wrap` — dropdown container for email options
- `.share-email-menu` — popover menu above email icon
- `#adobe-dc-view` — PDF viewer container; `height: calc(100vh - 100px)` on desktop, `min-height: calc(100vh - 50px)` on mobile/tablet to prevent PDF cutoff. Adobe `IN_LINE` embeds may scroll inside the viewer/iframe rather than the document viewport, which can prevent mobile browser address-bar auto-hide.
- `#footer-icons` — flex row on desktop and mobile/tablet

## Document Structure (LaTeX)

### Section Hierarchy
- `\section{}` for top-level sections (Title Case, unnumbered)
- No `\subsubsection`, `\paragraph`, or `\subparagraph`
- Blank lines precede and follow each `\section` command

### Abstract
- Standard `abstract` environment immediately after `\maketitle`
- Multi-paragraph abstracts are supported and used
- `tufte-handout` defines `abstract` as a `quotation` wrapper; this project overrides it in `base.tex` to add an “Abstract.” prefix and custom styling
- **Do not wrap abstract content in framing/boxing environments** (`framed`, `tcolorbox`, `mdframed`, `minipage`, etc.) — tufte-handout footnotes use `\marginpar`/sidenotes and will break inside boxes
- For decorative elements (e.g., a left vertical rule), use non-boxing techniques such as a `tikz`/`tikzmark` overlay with `remember picture` (safe for margin notes; requires multiple pdflatex passes, which `build.sh` already performs)

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
- **Footnote markers**: Use lining figures (`pplx`) for superscript footnote/citation markers to prevent misalignment of adjacent numbers; footnote body text retains default figures
- **Footnote placement**: Punctuation precedes footnote and citation markers (e.g., `text.\footnote{...}` not `text\footnote{...}.`)
- **Dashes**: Use `--` (LaTeX en dash) consistently in article source; avoid Unicode em dashes (`—`) for consistency

## CI/CD (`.github/workflows/`)

### `deploy.yml`
- Triggers on push to `master`
- `concurrency: deploy-master` (no cancel-in-progress) serializes deploy runs
- Runs in `texlive/texlive:latest` Docker container (has pdflatex, biber, Ghostscript, Python)
- `ADOBE_CLIENT_ID` injected from GitHub secret
- Python deps installed via OS packages: `python3-pil`, `python3-yaml`, `python3-jinja2`, `python3-pikepdf`
- Builds all articles, runs Pagefind for search indexing
- Commits built artifacts (PDFs, HTML, tags/) back to repo with `[skip ci]`
- Uses `git pull --rebase -X theirs origin master` before push (with fallback conflict resolution for generated files) to handle concurrent changes
- `git config --global --add safe.directory` required (Docker checkout owned by root, CI runs as UID 1001)
- `actions/configure-pages@v5` runs AFTER the commit step (running it before breaks git credential helpers)
- Deploys to GitHub Pages via `actions/upload-pages-artifact` from `_site/`

### `pr-check.yml`
- Triggers on PRs to `master` with `types: [opened, synchronize, reopened]`
- Uses `dorny/paths-filter` for shared files and `git diff` for changed `articles/*`; matrix builds only affected articles (or all if shared files change)
- Shared-path filter includes build/infra inputs such as `build.sh`, `base.tex`, `set-cropbox.py`, templates, generators, and `css/style.css`
- Python deps installed via OS packages: `python3-pil`, `python3-yaml`, `python3-jinja2`, `python3-pikepdf`
- Matrix/`if:` logic must use valid GitHub Actions expressions (e.g., `fromJson(...).include[0] != null`) and a proper matrix shape like `{"include":[{"article":"..."}]}`; invalid expressions (e.g., JQ-style `| length`) can cause GitHub to report spurious 0s push runs with “workflow file issue”
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

### OG/cover images silently missing for a published article
**Symptom**: `assets/og/{article}.png` (or `assets/fb/cover-*.png`) does not exist for an article with `status: published`, and the build prints no error.

**Cause (2026-10-27 → 2026-11-11)**: `build.sh` invoked the generator as `python3 … 2>/dev/null || true`, which hid every exception. A conflicted `git rebase --continue` on 2026-10-27 committed a `generate_og_images.py` that calls `add_border_and_ornaments()` but no longer defines it — the definition only ever existed in an uncommitted working-tree patch, and the `.bak` holding it was deleted during that same rebase (`rm generate_og_images.py.bak && git add -A`). Every build after that raised `NameError` and produced nothing, while the stale PNGs from before the rebase kept the site looking fine.

**Fix**: the function was recovered from the OpenCode session log (`~/.local/share/opencode/opencode.db`, session `ses_e8fd8a203ffe5XVufF3qTYaeQa`) and verified pixel-identical against the shipped cards. `build.sh` no longer redirects stderr, so a recurrence prints a traceback instead of failing silently. If images go missing again, run the generator by hand: `python3 generate_og_images.py`.

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
