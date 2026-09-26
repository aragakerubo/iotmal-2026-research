"""Write data/MANIFEST.md from the raw parquet files.

Usage::

    python scripts/manifest.py s3://<bucket>/raw/Yokohama
    python scripts/manifest.py /path/to/local/copy

Reads parquet footers only, so it runs in seconds from the JupyterLab
space. S3 access comes from pyarrow itself, using the space's execution
role; no extra package is needed.
"""

import sys
from datetime import date

import pandas as pd
from pyarrow import fs as pafs

from iotmal import manifest
from iotmal.paths import DATA_DIR, ensure_dir


def main(url: str) -> None:
    """Scan ``url``, compare with the paper's counts, write the manifest."""
    filesystem, root = pafs.FileSystem.from_uri(url)
    entries = manifest.scan(filesystem, root)
    paper = pd.read_csv(DATA_DIR / "paper_counts.csv")
    comparison = manifest.compare(entries, paper)

    out = ensure_dir(DATA_DIR) / "MANIFEST.md"
    out.write_text(
        f"# Raw data manifest\n\nScanned `{url}` on {date.today().isoformat()}. "
        "Footer facts only; no data was read.\n\n"
        "## Files\n\n"
        + manifest.render_markdown(entries)
        + "\n## Row counts against the paper (Table 5, Unknown excluded)\n\n"
        + manifest.render_comparison(comparison)
    )
    print(f"{len(entries)} parquet files -> {out}")
    print(manifest.render_comparison(comparison))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/manifest.py <s3://bucket/prefix | /local/dir>")
    main(sys.argv[1])
