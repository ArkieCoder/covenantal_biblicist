#!/usr/bin/env python3
"""Set CropBox per page: tight to content bounds (preserves annotations)."""

import pikepdf
import subprocess
import sys

pad = 2
TOP_PAD = 15
MIN_HEIGHT = 200
EXTRA_WHITESPACE_LAST_PAGE = 200  # Configurable amount of whitespace to add to bottom of last page (in points)
input_pdf = sys.argv[1] if len(sys.argv) > 1 else "main.pdf"
output_pdf = sys.argv[2] if len(sys.argv) > 2 else input_pdf.replace(".pdf", "-embed.pdf")

result = subprocess.run(
    ["gs", "-sDEVICE=bbox", "-dBATCH", "-dNOPAUSE", "-sOutputFile=/dev/null", input_pdf],
    capture_output=True, text=True)
bboxes = [l.split() for l in result.stderr.split("\n") if "HiResBoundingBox" in l]

pdf = pikepdf.open(input_pdf)
for i, page in enumerate(pdf.pages):
    lry = max(0, float(bboxes[i][2]) - pad)
    ury = float(bboxes[i][4]) + pad + TOP_PAD
    height = ury - lry
    if height < MIN_HEIGHT:
        lry = max(0, ury - MIN_HEIGHT)
    page.CropBox = pikepdf.Array([0, lry, 612, ury])
    page.MediaBox = pikepdf.Array([0, lry, 612, ury])

# Add extra whitespace to bottom of last page after cropping
if len(pdf.pages) > 0 and EXTRA_WHITESPACE_LAST_PAGE > 0:
    last_page = pdf.pages[-1]
    crop = last_page.CropBox
    media = last_page.MediaBox
    # Extend bottom edge downward (decrease lry in PDF coords adds space below)
    new_lry = float(crop[1]) - EXTRA_WHITESPACE_LAST_PAGE
    if new_lry < 0:
        new_lry = 0
    crop[1] = new_lry
    media[1] = new_lry
    last_page.CropBox = crop
    last_page.MediaBox = media

pdf.save(output_pdf)
