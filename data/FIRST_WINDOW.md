# First windows

Scanned `s3://iotmal-2026-research/raw/Yokohama` on 2026-10-05. For each prefix N, one row per binary: the canonical counts of its first N system calls, or of its whole trace when it made fewer. Counted over the live binaries of the split (inert and conflict set aside, D8), so the binary counts match `data/SPLIT.md`. A first window is the exact count vector.

| Calls | Arch | Distinct benign | Distinct malware | Shared by benign and malware |
| --- | --- | --- | --- | --- |
| 5 | arm | 1 | 15 | 0 |
| 5 | mips | 1 | 66 | 0 |
| 5 | mipsel | 1 | 56 | 1 |
| 5 | x86 | 1 | 45 | 0 |
| 10 | arm | 1 | 96 | 0 |
| 10 | mips | 1 | 131 | 0 |
| 10 | mipsel | 1 | 107 | 0 |
| 10 | x86 | 1 | 98 | 0 |
| 15 | arm | 11 | 146 | 0 |
| 15 | mips | 1 | 171 | 0 |
| 15 | mipsel | 1 | 139 | 0 |
| 15 | x86 | 1 | 141 | 0 |
| 20 | arm | 45 | 179 | 0 |
| 20 | mips | 136 | 202 | 0 |
| 20 | mipsel | 136 | 168 | 0 |
| 20 | x86 | 15 | 185 | 0 |

## Per family, first 20 calls

Signatures: exact = the first window's count vector; profile = the vector divided by its total, rounded to two decimals; presence = which calls occur at all. The second table counts windows shared by two family labels, malware families included.

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
| mipsel | Agent | 1 | 1 | 1 | 1 | 1 |
| mipsel | Rudedevil | 1 | 1 | 1 | 1 | 1 |
| x86 | Benign | 2554 | 15 | 15 | 14 | 1030 |
| x86 | Mirai | 1554 | 178 | 178 | 164 | 297 |
| x86 | DarkNexus | 50 | 5 | 5 | 5 | 42 |
| x86 | Generic | 12 | 3 | 3 | 3 | 10 |
| x86 | Gafgyt | 12 | 6 | 6 | 6 | 3 |

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
