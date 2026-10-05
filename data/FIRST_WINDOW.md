# First windows

Scanned `s3://iotmal-2026-research/raw/Yokohama` on 2026-10-05. One row per binary: the canonical counts of its first twenty system calls, or of its whole trace when it made fewer. Counted over the live binaries of the split (inert and conflict set aside, D8), so the binary counts match `data/SPLIT.md`.

Signatures: exact = the first window's count vector; profile = the vector divided by its total, rounded to two decimals; presence = which calls occur at all.

| Arch | Class | Binaries | Distinct exact | Distinct profile | Distinct presence | Largest exact group |
| --- | --- | --- | --- | --- | --- | --- |
| arm | Mirai | 1583 | 178 | 178 | 167 | 464 |
| arm | Benign | 150 | 45 | 45 | 30 | 18 |
| arm | DarkNexus | 41 | 1 | 1 | 1 | 41 |
| arm | Generic | 28 | 3 | 3 | 3 | 18 |
| arm | Gafgyt | 4 | 2 | 2 | 2 | 3 |
| arm | Tsunami | 3 | 1 | 1 | 1 | 3 |
| mips | Benign | 2601 | 136 | 136 | 84 | 617 |
| mips | Mirai | 1506 | 200 | 200 | 186 | 480 |
| mips | DarkNexus | 44 | 1 | 1 | 1 | 44 |
| mips | Gafgyt | 29 | 7 | 7 | 7 | 11 |
| mips | Generic | 2 | 1 | 1 | 1 | 2 |
| mipsel | Benign | 2496 | 136 | 136 | 83 | 574 |
| mipsel | Mirai | 1438 | 164 | 164 | 157 | 464 |
| mipsel | DarkNexus | 40 | 1 | 1 | 1 | 40 |
| mipsel | Gafgyt | 23 | 6 | 6 | 6 | 6 |
| mipsel | Generic | 4 | 1 | 1 | 1 | 4 |
| mipsel | Rudedevil | 1 | 1 | 1 | 1 | 1 |
| mipsel | Agent | 1 | 1 | 1 | 1 | 1 |
| x86 | Benign | 2554 | 15 | 15 | 14 | 1030 |
| x86 | Mirai | 1554 | 178 | 178 | 164 | 297 |
| x86 | DarkNexus | 50 | 5 | 5 | 5 | 42 |
| x86 | Gafgyt | 12 | 6 | 6 | 6 | 3 |
| x86 | Generic | 12 | 3 | 3 | 3 | 10 |

| Arch | Signature | Signatures shared across classes |
| --- | --- | --- |
| arm | exact | 3 |
| arm | presence | 3 |
| arm | profile | 3 |
| mips | exact | 6 |
| mips | presence | 6 |
| mips | profile | 6 |
| mipsel | exact | 6 |
| mipsel | presence | 7 |
| mipsel | profile | 6 |
| x86 | exact | 7 |
| x86 | presence | 7 |
| x86 | profile | 7 |

The table above counts first windows shared by two family labels, malware families included. Shared by a benign and a malware binary:

| Arch | Exact first windows shared by benign and malware |
| --- | --- |
| arm | 0 |
| mips | 0 |
| mipsel | 0 |
| x86 | 0 |
