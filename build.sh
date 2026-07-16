#!/bin/bash

# Build canonical version (full tufte layout)
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
rm -vf main.bcf main.out main.aux main.blg main.bbl main.log main.run.xml
mv main.pdf reach_men_reach_families.pdf

# Embed version (no headers, newpage at sections, variable page heights via CropBox)
pdflatex "\def\embedversion{} \input main.tex"
biber main
pdflatex "\def\embedversion{} \input main.tex"
pdflatex "\def\embedversion{} \input main.tex"

# Set CropBox per page: tight to content bounds (preserves annotations)
./set-cropbox.py main.pdf reach_men_reach_families-embed.pdf

rm -vf main.pdf main.bcf main.out main.aux main.blg main.bbl main.log main.run.xml
