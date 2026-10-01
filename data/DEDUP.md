# Near-duplicate binaries

Scanned `s3://iotmal-2026-research/raw/Yokohama` on 2026-10-01.

Signatures: exact = summed canonical count vector; profile = the vector divided by its total, rounded to two decimals; presence = which calls occur at all.

| Arch | Class | Binaries | Distinct exact | Distinct profile | Distinct presence | Largest exact group |
| --- | --- | --- | --- | --- | --- | --- |
| arm | Mirai | 2795 | 1326 | 967 | 476 | 559 |
| arm | Benign | 1980 | 154 | 147 | 103 | 1687 |
| arm | DarkNexus | 91 | 26 | 19 | 14 | 50 |
| arm | Generic | 29 | 29 | 26 | 16 | 1 |
| arm | Gafgyt | 5 | 5 | 4 | 4 | 1 |
| arm | Tsunami | 3 | 3 | 3 | 3 | 1 |
| arm | Agent | 1 | 1 | 1 | 1 | 1 |
| mips | Benign | 2617 | 2617 | 2565 | 1391 | 1 |
| mips | Mirai | 1616 | 1474 | 873 | 354 | 48 |
| mips | DarkNexus | 44 | 35 | 28 | 17 | 7 |
| mips | Gafgyt | 29 | 29 | 27 | 13 | 1 |
| mips | Generic | 2 | 2 | 2 | 2 | 1 |
| mipsel | Benign | 2511 | 2511 | 2463 | 1358 | 1 |
| mipsel | Mirai | 1534 | 1426 | 814 | 340 | 41 |
| mipsel | DarkNexus | 40 | 27 | 25 | 10 | 8 |
| mipsel | Gafgyt | 23 | 23 | 21 | 13 | 1 |
| mipsel | Generic | 4 | 4 | 4 | 2 | 1 |
| mipsel | Rudedevil | 1 | 1 | 1 | 1 | 1 |
| mipsel | Agent | 1 | 1 | 1 | 1 | 1 |
| x86 | Benign | 2570 | 2560 | 2512 | 1295 | 8 |
| x86 | Mirai | 1657 | 1282 | 804 | 383 | 190 |
| x86 | DarkNexus | 50 | 34 | 25 | 9 | 17 |
| x86 | Gafgyt | 12 | 12 | 11 | 6 | 1 |
| x86 | Generic | 12 | 12 | 10 | 4 | 1 |

| Arch | Signature | Signatures shared across classes |
| --- | --- | --- |
| arm | exact | 3 |
| arm | presence | 15 |
| arm | profile | 13 |
| mips | exact | 0 |
| mips | presence | 8 |
| mips | profile | 6 |
| mipsel | exact | 0 |
| mipsel | presence | 7 |
| mipsel | profile | 10 |
| x86 | exact | 1 |
| x86 | presence | 7 |
| x86 | profile | 8 |
