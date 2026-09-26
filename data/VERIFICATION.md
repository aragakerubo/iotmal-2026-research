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

| Class | Rows |
| --- | --- |
| Mirai | 507772 |
| Unknown | 113620 |
| Benign | 51791 |
| DarkNexus | 44156 |
| Gafgyt | 10450 |
| Generic | 9050 |
| Tsunami | 786 |
| Agent | 26 |

Columns with nulls: Std, Variance

### iotmal-2026-research/raw/Yokohama/arm/arm/Parquet Format/sar.parquet

| Class | Rows |
| --- | --- |
| Mirai | 320607 |
| Benign | 230367 |
| Unknown | 79613 |
| DarkNexus | 10399 |
| Generic | 3458 |
| Gafgyt | 595 |
| Tsunami | 359 |
| Agent | 120 |

### iotmal-2026-research/raw/Yokohama/arm/arm/Parquet Format/strace.parquet

| Class | Rows |
| --- | --- |
| Mirai | 20323388 |
| Benign | 878657 |
| DarkNexus | 505006 |
| Generic | 149191 |
| Gafgyt | 84316 |
| Tsunami | 48718 |
| Agent | 20 |

### iotmal-2026-research/raw/Yokohama/mips/mips/Parquet Format/pcap.parquet

| Class | Rows |
| --- | --- |
| Mirai | 602510 |
| Unknown | 149133 |
| Benign | 83968 |
| Gafgyt | 19580 |
| DarkNexus | 13578 |
| Generic | 1248 |

Columns with nulls: Std, Variance

### iotmal-2026-research/raw/Yokohama/mips/mips/Parquet Format/sar.parquet

| Class | Rows |
| --- | --- |
| Benign | 256545 |
| Mirai | 134186 |
| Unknown | 34210 |
| DarkNexus | 3590 |
| Gafgyt | 1833 |
| Generic | 176 |

Columns with nulls: network.net-dev[3].iface, network.net-dev[3].rxpck, network.net-dev[3].txpck, network.net-dev[3].rxkB, network.net-dev[3].txkB, network.net-dev[3].rxcmp, network.net-dev[3].txcmp, network.net-dev[3].rxmcst, network.net-dev[3].ifutil-percent, network.net-edev[3].iface, network.net-edev[3].rxerr, network.net-edev[3].txerr, network.net-edev[3].coll, network.net-edev[3].rxdrop, network.net-edev[3].txdrop, network.net-edev[3].txcarr, network.net-edev[3].rxfram, network.net-edev[3].rxfifo, network.net-edev[3].txfifo

### iotmal-2026-research/raw/Yokohama/mips/mips/Parquet Format/strace.parquet

| Class | Rows |
| --- | --- |
| Mirai | 22949149 |
| Benign | 6592302 |
| DarkNexus | 286968 |
| Gafgyt | 160459 |
| Generic | 4993 |

### iotmal-2026-research/raw/Yokohama/mipsel/mipsel/Parquet Format/pcap.parquet

| Class | Rows |
| --- | --- |
| Mirai | 568971 |
| Unknown | 425326 |
| Benign | 81254 |
| Gafgyt | 15903 |
| DarkNexus | 10421 |
| Generic | 1599 |
| Agent | 335 |
| Rudedevil | 207 |

Columns with nulls: Std, Variance

### iotmal-2026-research/raw/Yokohama/mipsel/mipsel/Parquet Format/sar.parquet

| Class | Rows |
| --- | --- |
| Benign | 251242 |
| Mirai | 130185 |
| Unknown | 129754 |
| DarkNexus | 3376 |
| Gafgyt | 1599 |
| Generic | 342 |
| Agent | 96 |
| Rudedevil | 85 |

Columns with nulls: network.net-dev[3].iface, network.net-dev[3].rxpck, network.net-dev[3].txpck, network.net-dev[3].rxkB, network.net-dev[3].txkB, network.net-dev[3].rxcmp, network.net-dev[3].txcmp, network.net-dev[3].rxmcst, network.net-dev[3].ifutil-percent, network.net-edev[3].iface, network.net-edev[3].rxerr, network.net-edev[3].txerr, network.net-edev[3].coll, network.net-edev[3].rxdrop, network.net-edev[3].txdrop, network.net-edev[3].txcarr, network.net-edev[3].rxfram, network.net-edev[3].rxfifo, network.net-edev[3].txfifo, filesystems[0].filesystem

### iotmal-2026-research/raw/Yokohama/mipsel/mipsel/Parquet Format/strace.parquet

| Class | Rows |
| --- | --- |
| Mirai | 21828458 |
| Benign | 5422828 |
| DarkNexus | 230391 |
| Gafgyt | 122211 |
| Generic | 11904 |
| Agent | 6297 |
| Rudedevil | 279 |

### iotmal-2026-research/raw/Yokohama/x86/x86/Parquet Format/pcap.parquet

| Class | Rows |
| --- | --- |
| Mirai | 319808 |
| Benign | 82622 |
| Unknown | 31531 |
| DarkNexus | 9938 |
| Gafgyt | 7666 |
| Generic | 4076 |

Columns with nulls: Std, Variance

### iotmal-2026-research/raw/Yokohama/x86/x86/Parquet Format/sar.parquet

| Class | Rows |
| --- | --- |
| Benign | 307852 |
| Mirai | 192440 |
| Unknown | 20570 |
| DarkNexus | 6000 |
| Generic | 1440 |
| Gafgyt | 910 |

Columns with nulls: interrupts[28].intr, network.net-dev[2].iface, network.net-dev[2].rxpck, network.net-dev[2].txpck, network.net-dev[2].rxkB, network.net-dev[2].txkB, network.net-dev[2].rxcmp, network.net-dev[2].txcmp, network.net-dev[2].rxmcst, network.net-dev[2].ifutil-percent, network.net-edev[2].iface, network.net-edev[2].rxerr, network.net-edev[2].txerr, network.net-edev[2].coll, network.net-edev[2].rxdrop, network.net-edev[2].txdrop, network.net-edev[2].txcarr, network.net-edev[2].rxfram, network.net-edev[2].rxfifo, network.net-edev[2].txfifo

### iotmal-2026-research/raw/Yokohama/x86/x86/Parquet Format/strace.parquet

| Class | Rows |
| --- | --- |
| Mirai | 19745632 |
| Benign | 5832881 |
| DarkNexus | 227611 |
| Gafgyt | 32777 |
| Generic | 15752 |
