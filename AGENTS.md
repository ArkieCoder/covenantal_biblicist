# AGENTS.md - LaTeX Conventions and Patterns

## Project Overview

- **Type**: LaTeX document project using `tufte-handout` class
- **Purpose**: Theological paper on complementarian ministry strategy
- **Build System**: pdflatex + biber via `build.sh`
- **Output**: `reach_men_reach_families.pdf`

## Document Structure

### Section Hierarchy
- Only `\section{}` is used (no `\subsection`, `\subsubsection`, `\paragraph`, or `\subparagraph`)
- Sections use Title Case for names
- Unnumbered by default (tufte-handout behavior)
- Blank lines precede and follow each `\section` command

### Abstract
- Standard `abstract` environment immediately after `\maketitle`
- Multi-paragraph abstracts are supported and used

### Preamble Organization
1. `\documentclass` with options
2. Package loading block
3. Custom field formats (QR codes)
4. Custom commands
5. Geometry overrides
6. Title metadata

## Custom Commands

### `\biblever{#1}` (line 25)
- **Purpose**: Format Bible verse references in small caps
- **Behavior**: Wraps in parentheses, applies `\MakeLowercase`, renders in `\textsc`
- **Usage**: `\biblever{gen. 1:1}` → `(GEN. 1:1)`

### `\scriptref{#1}` (lines 27-29)
- **Purpose**: Right-aligned scriptural attribution
- **Behavior**: Line break + right-aligned em-dash citation
- **Usage**: Called internally by `\scripture`

### `\scripture{text}{reference}` (lines 31-36)
- **Purpose**: Block scripture quotations with attribution
- **Behavior**: Wraps text in `quote` environment, appends right-aligned attribution
- **Usage**: `\scripture{In the beginning...}{Genesis 1:1}`

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

### Package Load Order
Content packages first, then infrastructure, then utility packages.

## Citation/Bibliography Style

- **Engine**: biber (not bibtex)
- **Style**: `biblatex` with `style=verbose`
  - First citation: full footnote citation
  - Subsequent citations: shortened form
- **Citation Command**: `\footcite{key}` (only citation command used)
- **Resource File**: `references.bib`

### QR Code Override
URLs in citations render as QR codes instead of text:
```latex
\DeclareFieldFormat{url}{
  \par\vspace{2pt}
  {\centering\qrcode[height=4.5em, level=H]{#1}\par}
}
```

## Typography Conventions

### Font Settings
- **Base size**: 9pt (via `fontsize` package)
- **Line spread**: `\linespread{1.25}` (25% more vertical space)
- **Effective leading**: 11.25pt

### Geometry
```latex
\geometry{
  left=0.5in,
  textwidth=33pc,
  marginparsep=1pc,
  marginparwidth=11pc,
  bottom=0.5in
}
```

### Emphasis Patterns
- **`\textit{}`**: Primary emphasis tool (used extensively)
- **`\textsc{}`**: Used in `\biblever` for verse references
- **Bold (`\textbf{}`)**: Never used
- **Underline**: Never used

## Formatting Patterns

### Definition-in-Footnote Pattern
New or loaded terms are defined in `\footnote{}` rather than inline:
- ESG and DEI expanded in footnote
- Complementarianism gets full paragraph footnote

### Inline Quotation
- Double quotation marks (`"..."`) for direct phrases or scare quotes
- No special quotation package loaded

### Paragraph Style
- Paragraphs separated by blank lines
- No indentation of first paragraph after headings
- Long, dense paragraphs with flowing essayistic style

## LaTeX Coding Style

### Comment Style
- `%%` double-percent comments for section dividers in preamble
- Single `%` not used in the file

### Whitespace Conventions
- Single blank line between logical blocks in preamble
- Blank lines separate paragraphs in body
- No structural indentation of LaTeX code

### Macro Definitions
- `%` at end of lines to suppress spurious whitespace
- Arguments referenced as `#1`, `#2` consistently
- Environments closed on same logical block with `%` after `\end`

### Line Length
- Source lines run as long as needed (no wrapping at specific column)

## Build System

### Pipeline
```bash
pdflatex main.tex      # First pass (resolves labels/references)
biber main             # Process bibliography
pdflatex main.tex      # Second pass (incorporates bibliography)
pdflatex main.tex      # Third pass (resolves remaining cross-references)
rm -vf main.bcf main.out main.aux main.blg main.bbl main.log main.run.xml
mv main.pdf reach_men_reach_families.pdf
```

### Dependencies
- TeX distribution (TeX Live/MacTeX) with:
  - `pdflatex`
  - `biber`
  - `tufte-handout` document class
  - All packages listed above

## Content Patterns

### Argumentative Essay Structure
1. Context/Background
2. Data
3. Problem
4. Solution

### Theological Vocabulary
- "covenant order"
- "sphere sovereignty"
- "complementarianism"
- "shepherd" (as a verb)

### Latin Usage
- `\textit{contra}` used for Latin phrases
- May use more in expanded versions

### Historical/Cultural Framing
- Establishes historical context before current issues
- References early 20th century (Machen) as foundation

## Notes for Editing

- The document is a **draft** - "Data" section lacks actual citations/data
- Bibliography contains only one entry (Machen, 1923)
- `\biblever` and `\scripture` commands are defined but not yet used
- `verse`, `gmverse`, and `alltt` packages are loaded but unused
- QR code feature is set up but unused (no URLs in bibliography yet)

## Build Commands

To compile the document:
```bash
bash build.sh
```

Or manually:
```bash
pdflatex main.tex && biber main && pdflatex main.tex && pdflatex main.tex
```
