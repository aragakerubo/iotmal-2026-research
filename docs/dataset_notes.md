# Dataset notes

Facts about the CIC-YNU-IoTMal 2026 download that the code depends on.
Every claim here was checked against the files, not the paper, unless it
says otherwise.

## Layout of the download

```
raw/Yokohama/
  Supplementary Information/   README_sup.pdf, Reading_parquet_strace.py,
                               combined.csv, description.xlsx
  arms/                        CSVs.tar.xz, Parquet Format.tar.xz, README_main.pdf
  codebase/                    CIC-YNU-IoTMal-Sandbox-main.zip
  mips/mips/                   CSVs/{pcap,sar}.csv, Parquet Format/{pcap,sar,strace}.parquet
  mipsel/mipsel/               same
  x86/x86/                     same
```

ARM arrives as a tarball under `arms/`; it has been extracted to
`arm/arm/Parquet Format/` to match the others. The manifest maps the
`arms` folder name to `arm` either way, so a parquet left under the
original folder would still be counted.

There are no raw `strace.log`, `sar.out` or `.pcap` files. The parquet
and CSV tables are the only form of the data, so any sequence model
depends on row order inside `strace.parquet` (checked in the
verification step).

## What one file holds

| Modality | Columns | Notes |
| --- | --- | --- |
| pcap | 42 | 40 pcap2csv features plus the shared columns |
| sar | 394 to 411 | Differs by architecture |
| strace | 130 to 135 | Differs by architecture: 130 on MIPS, 132 on MIPSEL, 135 on x86 |

The paper's Table 4 text attaches the "392 to 461" range to STRACE; the
files show it belongs to SAR. STRACE is one column per syscall name
plus the shared columns, and the per-architecture difference is the
alias problem (`mmap2` against `mmap` and so on) in concrete form.

## Missing values in strace.parquet

The authors' reader (`docs/supplementary/Reading_parquet_strace.py`)
unions the columns across row groups, reindexes every row group to that
union, and fills the resulting NaNs with the column's global mean. That
tells us two things. First, the file was assembled from pieces with
different column sets, so a NaN in a syscall column means "this syscall
did not occur in the piece this row came from", which is a count of
zero. Second, the published preprocessing replaced those zeros with the
mean count of the syscall across the whole file, which injects
distribution-wide information into every row. We fill with zero (D5).

## Unknown rows

`data/paper_counts.csv` is the authors' `combined.csv`: per-family row
counts per architecture and modality, excluding rows labelled Unknown.
Its sums reproduce Table 5 (MIPS strace 29,993,871 exactly). The file
row counts from the manifest exceed those sums by the number of Unknown
rows, which lands almost entirely in pcap and sar:

| Arch | pcap | sar | strace |
| --- | --- | --- | --- |
| mips | 149,133 (17.1%) | 34,210 (7.9%) | 0 |
| mipsel | 425,326 (38.5%) | 129,754 (25.1%) | 0 |
| x86 | 31,531 (6.9%) | 20,570 (3.9%) | 0 |

Dropping 38.5 percent of MIPSEL's network rows is a material choice and
goes in the paper's limitations. ARM's row is filled in by the first
manifest run against the extracted files.

Two small inconsistencies inside the paper itself: `combined.csv` sums
ARM strace to 21,989,296 where Table 5 prints 21,989,278, and ARM sar to
565,905 where Table 5 prints 565,909. We report the CSV's numbers, since
they are the authors' own data.
