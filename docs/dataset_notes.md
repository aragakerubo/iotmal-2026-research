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
| pcap | 42 | 39 flow features plus the shared columns, identical on every architecture |
| sar | 394 to 463 | 394 on MIPS and MIPSEL, 411 on x86, 463 on ARM |
| strace | 130 to 135 | 130 on MIPS, 132 on MIPSEL, 134 on ARM, 135 on x86 |

The paper's Table 4 text attaches the "392 to 461" range to STRACE; the
files show it belongs to SAR, and ARM exceeds it. STRACE is one column
per syscall name plus the shared columns, and the per-architecture
difference is the alias problem (`mmap2` against `mmap` and so on) in
concrete form.

Every file carries the same three shared columns: `Hash` (SHA-256 of
the binary, one string per row), `MalwareFamily`, `Arch`. There is no
timestamp, window index or sequence number, so row order inside the
file is the only possible carrier of sequence.

### STRACE columns

Named `Call_<syscall>`, one per syscall name as strace printed it. The
dtype marks the column's history: `int8` columns were present in every
piece the file was assembled from; `double` columns were missing from
at least one piece, because pandas promotes an integer column to float
when it must hold NaN. The row-level scan found no nulls in any STRACE
file, so the NaNs were filled before release; the fill check in the
same scan (non-integer values in `double` count columns) says whether
the fill was the column mean, as the authors' reader does. Across the four
files there are 181 distinct names; 23 of them are truncated (`Call_g`,
`Call_readlin`, `Call_wri`, ...), syscall names cut off at a log
boundary, and one is an undecoded number (`Call_syscall_0x193`, which is
`clock_gettime64` in the 32-bit ARM table). D6 and
`configs/syscall_canonical.yaml` fold the ABI aliases and the
unambiguous fragments onto 132 canonical names and drop the rest;
`data/syscall_resolution.csv` lists the outcome for every raw column and
`data/syscall_vocabulary.csv` which architectures feed each canonical
name.

Row groups hold about a million rows each (21 on ARM, 29 on MIPS, 27
on MIPSEL, 25 on x86). Every binary's rows are one unbroken block in
every file, and the number of binaries that straddle a row-group
boundary is always `row groups minus one`, so the groups are plain
chunks of a file that was already ordered by binary.

### Windows overlap by construction

Each STRACE row counts the previous twenty calls and there is one row
per call from the twentieth onward, so a binary with `w` windows has a
trace of `w + 19` calls, and consecutive rows share nineteen of their
twenty calls. Adjacent rows are 95 percent identical before any model
sees them, which is why a row-level random split measures memorisation:
a test row's near-twin is almost always in the training set. ARM's
median of 18 windows is a trace of 37 calls.

### Inert executions on ARM

The near-duplicate scan (`data/DEDUP.md`) found that 1,687 of ARM's
1,980 benign binaries share one summed syscall vector and 560 of its
2,795 Mirai binaries share another. The benign one is 16 windows, a
trace of about 35 calls, consisting of `execve`, the loader's `open`,
`fstat`, `mmap`, `mprotect`, `close`, `fcntl`, `set_thread_area` and
`set_tid_address`, one `writev` and `exit_group`: a dynamically linked
program that failed at startup and printed an error. The Mirai one is
4 windows, about 23 calls: `execve`, `getpid`, `writev`, `exit_group`,
a static binary that printed and quit. On the other three architectures
the benign class is almost entirely distinct (2,617 of 2,617 on MIPS)
and the largest identical Mirai group is 190 (x86). D8 excludes inert
binaries and records the counts.

### Binaries, not rows

Rows per binary are extremely skewed in STRACE: on ARM the median
binary has 18 windows and the largest 106,660; on MIPS the median is
1,592 and the largest 184,253. Class balance and the hash-grouped split
therefore have to be planned on binaries per class (in
`data/VERIFICATION.md`), and a per-binary window cap is what keeps a
handful of long-running Mirai samples from being most of the training
set. SAR's median of 95 to 120 rows per binary at one sample per second
puts a typical execution at about two minutes.

### PCAP columns

The 39 features are CIC's standard flow set, the same as CICIoT2023:
`Header_Length`, `Protocol Type`, `Time_To_Live`, `Rate`, seven flag
ratios and four flag counts, fifteen protocol indicator shares (`HTTP`,
`HTTPS`, `DNS`, `Telnet`, `SMTP`, `SSH`, `IRC`, `TCP`, `UDP`, `DHCP`,
`ARP`, `ICMP`, `IGMP`, `IPv`, `LLC`), packet-size statistics (`Tot sum`,
`Min`, `Max`, `AVG`, `Std`, `Tot size`, `Number`, `Variance`) and `IAT`.
There is no source or destination address, no port and no hostname, so
nothing in the released features encodes where the benign programs'
traffic went. Two columns can still act as sandbox fingerprints and get
an ablation: `DNS` (the benign prompt resolves google.com and bing.com;
Mirai scans raw addresses) and `Time_To_Live` (replies from the internet
against replies from the internal range).

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
| arm | 113,620 (15.4%) | 79,613 (12.3%) | 0 |
| mips | 149,133 (17.1%) | 34,210 (7.9%) | 0 |
| mipsel | 425,326 (38.5%) | 129,754 (25.1%) | 0 |
| x86 | 31,531 (6.9%) | 20,570 (3.9%) | 0 |

Dropping 38.5 percent of MIPSEL's network rows is a material choice and
goes in the paper's limitations. `data/MANIFEST.md` holds the scan these
numbers come from; `data/VERIFICATION.md` (the row-level scan) confirms
them from the label column itself.

Two small inconsistencies inside the paper itself: `combined.csv` sums
ARM strace to 21,989,296 where Table 5 prints 21,989,278, and ARM sar to
565,905 where Table 5 prints 565,909. We report the CSV's numbers, since
they are the authors' own data.
