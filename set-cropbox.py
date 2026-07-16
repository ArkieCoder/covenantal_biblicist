#!/usr/bin/env python3
"""Set CropBox per page: tight to content bounds (preserves annotations)."""

import pikepdf
import subprocess
import sys

pad = 2
input_pdf = sys.argv[1] if len(sys.argv) > 1 else "main.pdf"
output_pdf = sys.argv[2] if len(sys.argv) > 2 else "reach_men_reach_families-embed.pdf"

result = subprocess.run(
    ["gs", "-sDEVICE=bbox", "-dBATCH", "-dNOPAUSE", "-sOutputFile=/dev/null", input_pdf],
    capture_output=True, text=True)
bboxes = [l.split() for l in result.stderr.split("\n") if "HiResBoundingBox" in l]

pdf = pikepdf.open(input_pdf)
for i, page in enumerate(pdf.pages):
    lry = max(0, float(bboxes[i][2]) - pad)
    ury = float(bboxes[i][4]) + pad
    page.CropBox = pikepdf.Array([0, lry, 612, ury])
pdf.save(output_pdf)
