#!/bin/bash

pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
rm -vf main.bcf main.out main.aux main.blg main.bbl main.log main.run.xml
mv main.pdf reach_men_reach_families.pdf
