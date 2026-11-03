# Arm A ratio table — synthetic population, known true surface (200 days, R=25 draws/day)

Grid RMSE pooled (bps of IV) and ratio vs SRS [95% whole-day cluster bootstrap CI].
Paper values (NVDA corpus, author-reported) shown for orientation only; magnitudes are not the claim.

| Target | α | SRS | Neyman | EqCell | PPS | Neyman/SRS | EqCell/SRS | PPS/SRS |
|---|---|---|---|---|---|---|---|---|
| EW | 0.25 | 288.5 | 237.6 | 209.4 | 478.8 | 0.82 [0.81, 0.84] | 0.73 [0.71, 0.74] | 1.66 [1.63, 1.69] |
| LW | 0.25 | 303.9 | 253.2 | 219.5 | 247.8 | 0.83 [0.82, 0.85] | 0.72 [0.71, 0.74] | 0.81 [0.79, 0.84] |
| EW | 0.4 | 198.4 | 165.2 | 134.6 | 365.7 | 0.83 [0.82, 0.85] | 0.68 [0.67, 0.69] | 1.84 [1.81, 1.88] |
| LW | 0.4 | 212.6 | 176.5 | 141.5 | 156.6 | 0.83 [0.82, 0.84] | 0.67 [0.65, 0.68] | 0.74 [0.71, 0.77] |
| EW | 0.6 | 129.8 | 101.5 | 76.4 | 253.9 | 0.78 [0.77, 0.80] | 0.59 [0.58, 0.60] | 1.96 [1.92, 1.99] |
| LW | 0.6 | 140.3 | 107.3 | 79.4 | 85.6 | 0.77 [0.74, 0.78] | 0.57 [0.55, 0.58] | 0.61 [0.58, 0.64] |
| EW | 0.8 | 77.9 | 55.8 | 34.9 | 158.3 | 0.72 [0.70, 0.73] | 0.45 [0.44, 0.46] | 2.03 [2.00, 2.07] |
| LW | 0.8 | 83.6 | 58.1 | 35.2 | 41.8 | 0.69 [0.68, 0.72] | 0.42 [0.40, 0.44] | 0.50 [0.48, 0.52] |

Stratum coverage (first draw of each day, mean fraction of present cells hit): α=0.25: SRS 0.997, Neyman 1.000, EqCell 1.000, PPS 0.989; α=0.4: SRS 1.000, Neyman 1.000, EqCell 1.000, PPS 1.000; α=0.6: SRS 1.000, Neyman 1.000, EqCell 1.000, PPS 1.000; α=0.8: SRS 1.000, Neyman 1.000, EqCell 1.000, PPS 1.000

Population: 111573 contracts over 200 days, median 534/day. Seed 20261103.
