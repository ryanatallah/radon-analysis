"""Build index.html — a clean, shareable report from radon.ipynb.

Runs the whole notebook (so data + helpers are computed), then renders an
HTML page that:
  - hides all code cells (presentation only),
  - renders Plotly charts as interactive HTML (loaded from the Plotly CDN),
  - drops the setup sections listed in HIDE_HEADERS below.

Re-run after editing the notebook:  python build_report.py
"""

import re

import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor
from traitlets.config import Config

SOURCE_NB = "radon.ipynb"
OUTPUT_HTML = "index.html"
PAGE_TITLE = "Radon Analysis"

# Markdown section headers to hide from the report (the header cell AND the
# code/output cells beneath it, up to the next markdown header). They still
# execute — they're just not shown.
HIDE_HEADERS = {
    "## Load data",
    "## Helper: chart annotations",
}

nb = nbformat.read(SOURCE_NB, as_version=4)

# Make Plotly emit self-contained HTML (CDN-loaded plotly.js) so figures
# render in a static page instead of the notebook-only JSON mimetype.
nb.cells.insert(
    1,
    nbformat.v4.new_code_cell(
        "import plotly.io as pio\npio.renderers.default = 'notebook_connected'"
    ),
)

# Tag the setup sections so the exporter removes them from the output.
cells = nb.cells
i = 0
while i < len(cells):
    c = cells[i]
    if c.cell_type == "markdown" and c.source.strip().splitlines():
        if c.source.strip().splitlines()[0].strip() in HIDE_HEADERS:
            c.metadata.setdefault("tags", []).append("remove-cell")
            j = i + 1
            while j < len(cells) and cells[j].cell_type != "markdown":
                cells[j].metadata.setdefault("tags", []).append("remove-cell")
                j += 1
            i = j
            continue
    i += 1

# Execute the full notebook (all cells, including hidden ones).
ExecutePreprocessor(timeout=300, kernel_name="python3").preprocess(
    nb, {"metadata": {"path": "."}}
)

# Render: hide code input, strip tagged cells.
config = Config()
config.TagRemovePreprocessor.remove_cell_tags = ("remove-cell",)
config.TagRemovePreprocessor.enabled = True

exporter = HTMLExporter(config=config)
exporter.exclude_input = True

body, _ = exporter.from_notebook_node(nb)
body = re.sub(r"<title>.*?</title>", f"<title>{PAGE_TITLE}</title>", body, count=1)

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(body)

print(f"Wrote {OUTPUT_HTML}")
