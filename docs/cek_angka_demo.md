# Demo number audit — D0

Checked against the local Sectors fixtures and processed CSVs on 7 October 2026.
CSV snapshots are from 30 September; B0 financial supplements are from 6 October.
Do not present these as live market figures. Source dates and observation windows remain visible in cards.

| Scenario / number in FINAL_PLAN §6 | Number in available data | Source / field | Assessment |
|---|---|---|---|
| MGLV start Rp600 | Rp600, 26 Sep 2025 | fixtures/MGLV/harga_harian.json, close/date | Matches; start is not the window minimum |
| MGLV last Rp14,650 | Rp14,650, 29 Sep 2026 | same file, latest close | Matches snapshot |
| MGLV approximately 24× | 14,650 / 600 = 24.42× | derived from sourced endpoints | Matches rounded illustration |
| MGLV 7 suspensions | 7, latest 9 Sep 2026 | fixtures/MGLV/suspensi.json, results | Matches |
| MGLV 6 price-related suspensions | 6 reasons mention cumulative price increases; 1 listing-fee delay | same file, reason | Matches |
| MGLV Monitoring Board Apr 2026 | 6–15 Apr 2026, criterion 10, no longer active in snapshot | papan_pemantauan_khusus.csv | Matches historical episode; criterion 10 removed 28 Sep |
| MGLV Nextier 78.74% → 62.71% | 0.7874 → 0.6271 in ordered sale filings | fixtures/MGLV/filings.json, share_percentage_before/after | Matches; divided by 100 in parser |
| MGLV approximately 1,389 holders | 1,389, 31 Aug 2026 | komposisi_pemegang_saham.csv, jumlah_pemegang | Matches; not a September observation |
| MGLV rights issue ex 2 Nov | 2 Nov 2026 | kalender_aksi_korporasi.csv, tanggal | Matches calendar snapshot |
| MGLV exercise Rp8,880 | Rp8,880, ratio 100 old : 15 new | same file, detail_json | Matches; comparison close has a separate source date |
| MDKA 82% nickel | 82.39%, financial year 2024 | segmen_pendapatan.csv, Nickel Project/porsi | Matches rounded value |
| MDKA gold correlation 0.40 | 0.40, moderate | saham_vs_komoditas.csv, Gold/korelasi_bulanan | Matches; correlation of monthly changes |
| MDKA copper correlation 0.46 | 0.46, moderate | same file, Copper/korelasi_bulanan | Matches |
| MDKA return −36% | −35.79% | same file, total_return_saham | Matches; total return, not unadjusted price return |
| Gold change +132% | +132.40%, Jan 2023–Aug 2026 | same file, Gold/perubahan_komoditas | Matches; World Bank prices |
| ANTM 68/70 buy | 68 buy, 2 hold, 70 recommendations, 1 Sep 2026 | rating_analis.csv | Numbers match; “all” does not. Use “most” for a matching claim |
| ANTM 2026 EPS −46% | −46.2737% | same file, proyeksi_pertumbuhan_eps | Matches rounded projection; label as analysts' estimate |
| ANTM revenue −30% | −30.2714% | same file, proyeksi_pertumbuhan_pendapatan | Matches rounded projection |
| BUMI 226k → 590k holders | 226,137 → 590,547, Sep 2025–May 2026 | komposisi_pemegang_saham.csv, jumlah_pemegang | Matches historical endpoints, outside current six-observation window |
| BUMI retail 13% → 24% | 13.21% → 23.46%, same historical endpoints | same file, porsi_ritel_lokal | Approximate; May endpoint rounds to 23% at whole-percent precision |
| BUMI foreign 81% → 69% | 81.07% → 69.95% at May; 68.95% at Aug 2026 | same file, porsi_asing | Plan mixes endpoints; show exact dates |
| BUMI current retail-surge claim | Mar–Aug 2026: retail 22.40% → 23.99%, holders 591,364 → 546,718 | same file, latest six rows | Mixed signals: proposed P-1 returns misleading, not unqualified matching |
| BUMI “foreigners entering” | Latest daily flow and monthly ownership decline do not support it | fixtures/BUMI/aliran_asing.json and komposisi_pemegang.json | Not matching; monthly fallback independently tested |
| PSAB yield 25% | 25.7143%, report date 6 Oct 2026 | fixtures/PSAB/report.json, dividend.yield_ttm | Within existing D-1 tolerance; snapshot updated after plan |
| PSAB payout 114% | 114.4974% | same file, payout_ratio | Matches rounded value; D-2 warning retained alongside D-1 claim |
| Backup ticker under 15% free float | BREN 12.693%, snapshot 30 Sep 2026 | radar_free_float.csv | Eligible backup; F-1 finding activates Radar |
| BREN 2027 deadline / absorption | 31 Mar 2027, approximately 79.66 trading days | same file; recomputed by R-1 | Matches; scenario 6 has no exact number in §6 |

Additional context in §3.4: MGLV's 60-observation close × volume average is
Rp12,924,715,166.67 (about Rp12.9 billion/day). It exceeds proposed Q-1's
Rp1 billion/day threshold, so no low-liquidity warning is shown for that snapshot.

## Implementation decisions

- N-1 is proposed: literal “all” requires 100%; “most” requires at least 90%.
- P-1 is proposed: retail share must rise at least 1 percentage point and holder count must rise for `sesuai`.
  A single rising indicator produces `menyesatkan`. Six observations means March–August, not an invented September–May window.
- CSV retail shares use total company shares. Direction uses retail divided by coverage, consistent with A-2's recorded-share denominator;
  cards display raw shares and coverage explicitly. Cross-company comparisons are unsupported.
- Q-1 and C-1 are proposed contextual rules. Q-1 uses 60 observations and Rp1 billion/day; C-1 uses the next 90 calendar days.
- The commodity segment map covers every segment in the supplied Sectors revenue CSV. It is a manual company-specific classification.
  MDKA's Tujuh Bukit project is mixed gold/copper and contributes to neither pure commodity share.
  MBMA's manufacturing/mining segments are classified as nickel; ADMR's mining segment as coal.
  Unclassified services/other segments remain `lainnya`; missing segments return unavailable rather than zero.
- Commodity relationship rows without revenue or total-return fields retain nulls. K-1 can operate on known revenue without correlation context.
- No supply-chain positioning is added: the plan leaves that optional decision open and the supplied data does not establish sourced positions.
- D5/D6 recording and publishing are excluded from this implementation request.

The original FINAL_PLAN remains a historical plan. Scenario tests use the literal claims and the documented current window;
they do not force data or verdicts to match the earlier script.
