#!/bin/bash

# Build canonical version (full tufte layout)
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
rm -vf main.bcf main.out main.aux main.blg main.bbl main.log main.run.xml
mv main.pdf reach_men_reach_families.pdf

# Embed version (no headers, newpage at sections, pdfcrop to variable page heights)
pdflatex "\def\embedversion{} \input main.tex"
biber main
pdflatex "\def\embedversion{} \input main.tex"
pdflatex "\def\embedversion{} \input main.tex"
pdfcrop --margins 1 main.pdf embed-cropped.pdf

# Normalize all page widths to 612pt (pdfcrop trims width to content bounding box)
gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -dCompressPages=false -dASCII85EncodePages=false -sOutputFile=embed-dec.pdf embed-cropped.pdf
LC_ALL=C sed -i '' 's|/MediaBox \[0 0 [0-9]* \([0-9]*\)\]|/MediaBox [0 0 612 \1]|g' embed-dec.pdf
gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=reach_men_reach_families-embed.pdf embed-dec.pdf
rm -f embed-cropped.pdf embed-dec.pdf

rm -vf main.pdf main.bcf main.out main.aux main.blg main.bbl main.log main.run.xml
