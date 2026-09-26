# Dataset verification

Scanned `s3://iotmal-2026-research/raw/Yokohama` on 2026-09-26.

| Path | Rows | Row groups | Unknown | Hash | Distinct hashes | Runs | Contiguous | Spanning groups | Rows/hash min | median | max | Null columns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iotmal-2026-research/raw/Yokohama/arm/arm/Parquet Format/pcap.parquet | 737651 | 1 | 113620 | yes | 5599 | 5599 | yes | 0 | 2 | 27 | 41171 | 2 |
| iotmal-2026-research/raw/Yokohama/arm/arm/Parquet Format/sar.parquet | 645518 | 1 | 79613 | yes | 5467 | 5467 | yes | 0 | 1 | 119 | 179 | 0 |
| iotmal-2026-research/raw/Yokohama/arm/arm/Parquet Format/strace.parquet | 21989296 | 21 | 0 | yes | 4904 | 4904 | yes | 20 | 4 | 18 | 106660 | 0 |
| iotmal-2026-research/raw/Yokohama/mips/mips/Parquet Format/pcap.parquet | 870017 | 1 | 149133 | yes | 4709 | 4709 | yes | 0 | 18 | 37 | 15175 | 2 |
| iotmal-2026-research/raw/Yokohama/mips/mips/Parquet Format/sar.parquet | 430540 | 1 | 34210 | yes | 4438 | 4438 | yes | 0 | 1 | 95 | 167 | 19 |
| iotmal-2026-research/raw/Yokohama/mips/mips/Parquet Format/strace.parquet | 29993871 | 29 | 0 | yes | 4308 | 4308 | yes | 28 | 6 | 1592.5 | 184253 | 0 |
| iotmal-2026-research/raw/Yokohama/mipsel/mipsel/Parquet Format/pcap.parquet | 1104016 | 2 | 425326 | yes | 5490 | 5490 | yes | 1 | 7 | 53 | 15430 | 2 |
| iotmal-2026-research/raw/Yokohama/mipsel/mipsel/Parquet Format/sar.parquet | 516679 | 1 | 129754 | yes | 5246 | 5246 | yes | 0 | 1 | 98 | 199 | 20 |
| iotmal-2026-research/raw/Yokohama/mipsel/mipsel/Parquet Format/strace.parquet | 27622368 | 27 | 0 | yes | 4114 | 4114 | yes | 26 | 3 | 1602.5 | 178125 | 0 |
| iotmal-2026-research/raw/Yokohama/x86/x86/Parquet Format/pcap.parquet | 455641 | 1 | 31531 | yes | 4475 | 4475 | yes | 0 | 2 | 35 | 2192 | 2 |
| iotmal-2026-research/raw/Yokohama/x86/x86/Parquet Format/sar.parquet | 529212 | 1 | 20570 | yes | 4435 | 4435 | yes | 0 | 1 | 120 | 155 | 20 |
| iotmal-2026-research/raw/Yokohama/x86/x86/Parquet Format/strace.parquet | 25854653 | 25 | 0 | yes | 4301 | 4301 | yes | 24 | 3 | 1152 | 175532 | 0 |

### iotmal-2026-research/raw/Yokohama/arm/arm/Parquet Format/pcap.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Mirai | 507772 | 2795 |
| Unknown | 113620 | 695 |
| Benign | 51791 | 1980 |
| DarkNexus | 44156 | 91 |
| Gafgyt | 10450 | 5 |
| Generic | 9050 | 29 |
| Tsunami | 786 | 3 |
| Agent | 26 | 1 |

Columns with nulls: Std, Variance

No non-integer values in any `double` count column (row groups 0).

### iotmal-2026-research/raw/Yokohama/arm/arm/Parquet Format/sar.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Mirai | 320607 | 2721 |
| Benign | 230367 | 1945 |
| Unknown | 79613 | 675 |
| DarkNexus | 10399 | 88 |
| Generic | 3458 | 29 |
| Gafgyt | 595 | 5 |
| Tsunami | 359 | 3 |
| Agent | 120 | 1 |

No non-integer values in any `double` count column (row groups 0).

### iotmal-2026-research/raw/Yokohama/arm/arm/Parquet Format/strace.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Mirai | 20323388 | 2795 |
| Benign | 878657 | 1980 |
| DarkNexus | 505006 | 91 |
| Generic | 149191 | 29 |
| Gafgyt | 84316 | 5 |
| Tsunami | 48718 | 3 |
| Agent | 20 | 1 |

No non-integer values in any `double` count column (row groups 0, 10, 20).

### iotmal-2026-research/raw/Yokohama/mips/mips/Parquet Format/pcap.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Mirai | 602510 | 1616 |
| Unknown | 149133 | 401 |
| Benign | 83968 | 2617 |
| Gafgyt | 19580 | 29 |
| DarkNexus | 13578 | 44 |
| Generic | 1248 | 2 |

Columns with nulls: Std, Variance

No non-integer values in any `double` count column (row groups 0).

### iotmal-2026-research/raw/Yokohama/mips/mips/Parquet Format/sar.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Benign | 256545 | 2433 |
| Mirai | 134186 | 1544 |
| Unknown | 34210 | 393 |
| DarkNexus | 3590 | 42 |
| Gafgyt | 1833 | 24 |
| Generic | 176 | 2 |

Columns with nulls: network.net-dev[3].iface, network.net-dev[3].rxpck, network.net-dev[3].txpck, network.net-dev[3].rxkB, network.net-dev[3].txkB, network.net-dev[3].rxcmp, network.net-dev[3].txcmp, network.net-dev[3].rxmcst, network.net-dev[3].ifutil-percent, network.net-edev[3].iface, network.net-edev[3].rxerr, network.net-edev[3].txerr, network.net-edev[3].coll, network.net-edev[3].rxdrop, network.net-edev[3].txdrop, network.net-edev[3].txcarr, network.net-edev[3].rxfram, network.net-edev[3].rxfifo, network.net-edev[3].txfifo

No non-integer values in any `double` count column (row groups 0).

### iotmal-2026-research/raw/Yokohama/mips/mips/Parquet Format/strace.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Mirai | 22949149 | 1616 |
| Benign | 6592302 | 2617 |
| DarkNexus | 286968 | 44 |
| Gafgyt | 160459 | 29 |
| Generic | 4993 | 2 |

No non-integer values in any `double` count column (row groups 0, 14, 28).

### iotmal-2026-research/raw/Yokohama/mipsel/mipsel/Parquet Format/pcap.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Mirai | 568971 | 1534 |
| Unknown | 425326 | 1376 |
| Benign | 81254 | 2511 |
| Gafgyt | 15903 | 23 |
| DarkNexus | 10421 | 40 |
| Generic | 1599 | 4 |
| Agent | 335 | 1 |
| Rudedevil | 207 | 1 |

Columns with nulls: Std, Variance

No non-integer values in any `double` count column (row groups 0, 1).

### iotmal-2026-research/raw/Yokohama/mipsel/mipsel/Parquet Format/sar.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Benign | 251242 | 2375 |
| Mirai | 130185 | 1483 |
| Unknown | 129754 | 1322 |
| DarkNexus | 3376 | 39 |
| Gafgyt | 1599 | 21 |
| Generic | 342 | 4 |
| Agent | 96 | 1 |
| Rudedevil | 85 | 1 |

Columns with nulls: network.net-dev[3].iface, network.net-dev[3].rxpck, network.net-dev[3].txpck, network.net-dev[3].rxkB, network.net-dev[3].txkB, network.net-dev[3].rxcmp, network.net-dev[3].txcmp, network.net-dev[3].rxmcst, network.net-dev[3].ifutil-percent, network.net-edev[3].iface, network.net-edev[3].rxerr, network.net-edev[3].txerr, network.net-edev[3].coll, network.net-edev[3].rxdrop, network.net-edev[3].txdrop, network.net-edev[3].txcarr, network.net-edev[3].rxfram, network.net-edev[3].rxfifo, network.net-edev[3].txfifo, filesystems[0].filesystem

No non-integer values in any `double` count column (row groups 0).

### iotmal-2026-research/raw/Yokohama/mipsel/mipsel/Parquet Format/strace.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Mirai | 21828458 | 1534 |
| Benign | 5422828 | 2511 |
| DarkNexus | 230391 | 40 |
| Gafgyt | 122211 | 23 |
| Generic | 11904 | 4 |
| Agent | 6297 | 1 |
| Rudedevil | 279 | 1 |

No non-integer values in any `double` count column (row groups 0, 13, 26).

### iotmal-2026-research/raw/Yokohama/x86/x86/Parquet Format/pcap.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Mirai | 319808 | 1657 |
| Benign | 82622 | 2570 |
| Unknown | 31531 | 174 |
| DarkNexus | 9938 | 50 |
| Gafgyt | 7666 | 12 |
| Generic | 4076 | 12 |

Columns with nulls: Std, Variance

No non-integer values in any `double` count column (row groups 0).

### iotmal-2026-research/raw/Yokohama/x86/x86/Parquet Format/sar.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Benign | 307852 | 2570 |
| Mirai | 192440 | 1620 |
| Unknown | 20570 | 173 |
| DarkNexus | 6000 | 50 |
| Generic | 1440 | 12 |
| Gafgyt | 910 | 10 |

Columns with nulls: interrupts[28].intr, network.net-dev[2].iface, network.net-dev[2].rxpck, network.net-dev[2].txpck, network.net-dev[2].rxkB, network.net-dev[2].txkB, network.net-dev[2].rxcmp, network.net-dev[2].txcmp, network.net-dev[2].rxmcst, network.net-dev[2].ifutil-percent, network.net-edev[2].iface, network.net-edev[2].rxerr, network.net-edev[2].txerr, network.net-edev[2].coll, network.net-edev[2].rxdrop, network.net-edev[2].txdrop, network.net-edev[2].txcarr, network.net-edev[2].rxfram, network.net-edev[2].rxfifo, network.net-edev[2].txfifo

No non-integer values in any `double` count column (row groups 0).

### iotmal-2026-research/raw/Yokohama/x86/x86/Parquet Format/strace.parquet

| Class | Rows | Binaries |
| --- | --- | --- |
| Mirai | 19745632 | 1657 |
| Benign | 5832881 | 2570 |
| DarkNexus | 227611 | 50 |
| Gafgyt | 32777 | 12 |
| Generic | 15752 | 12 |

No non-integer values in any `double` count column (row groups 0, 12, 24).
