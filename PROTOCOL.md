# Frozen protocol — recorded BEFORE any design comparison was run (2026-11-03, test stage)

Implements experiment-plan.md exactly. Deviations from the paper are listed at the end;
population parameters below were fixed before the first comparative run and were not
tuned after seeing results (stop condition 2).

## Arm A — surface sampling (paper §3.1, §3.2 protocol, verbatim where applicable)

- Grid: moneyness [0.60,0.90) [0.90,1.00) [1.00,1.10) [1.10,1.40); maturity [7,30) [30,90) [90,366) days. H=12.
- n_t = round(alpha * N_t), alpha in {0.25, 0.40, 0.60, 0.80}.
- Designs: SRS; Liquidity PPS (size w_i = (Vol_i+1)/(RelSpread_i + 1e-4), pi via iterative
  certainty capping pi=min(1,c*M), Madow single-start systematic sampling on a randomly
  permuted frame); plug-in Neyman (n_h prop. N_h * S_{h,t-1}); plug-in equal-cell
  (n_h prop. S_{h,t-1}); stratified allocations bounded 1 <= n_h <= N_h via water-filling +
  largest-remainder rounding; within-stratum SRSWOR, pi_i = n_h/N_h. S_{h,t-1} = prior day's
  within-cell sd of observed IV (day 1: cross-cell mean dispersion).
- Estimators: EW target = Hajek per cell (Eq. 7); LW target = Horvitz-Thompson ratio per
  cell with weights w_i (Eq. 8). Benchmarks: full-population cell means (EW) and
  w-weighted cell means (LW). Empty-cell imputation: global design-weighted sample mean
  (weights 1/pi for EW, w_i/pi for LW), per paper.
- Accuracy: RMSE_t = equal-cell RMSE across present cells for draw r; RMSE_pool = mean of
  RMSE_t over days and draws (Eq. 9), reported in bps of IV. Ratios vs SRS with 1,000-replicate
  whole-day cluster bootstrap (days resampled jointly across designs).

### Synthetic population (frozen parameters)

- T = 200 days, seed 20261103. R = 25 Monte Carlo draws per day per design per alpha.
- True surface: sigma(m, tau) = L_t + a_t*(m-1) + b_t*(m-1)^2 + d_t*(1 - exp(-tau/90)),
  clipped to (0.05, 3.00). Day parameters: L_t AR(1) mean 0.34, phi 0.85, sd 0.045;
  a_t ~ N(-0.55, 0.10) (put skew); b_t ~ N(1.6, 0.35); d_t ~ N(-0.05, 0.015).
- Contracts/day: N_t = clip(round(exp(N(log 550, 0.35))), 300, 900).
- Moneyness: m = clip(1 + 0.115 * t_4, 0.60, 1.399). DTE: clip(round(exp(N(log 48, 0.75))), 7, 365).
- Volume: log Vol ~ N(2.6 - 3.2*|m-1| - 0.004*DTE, 0.95), floored at 0.
- RelSpread: clip(0.012 + 0.30*|m-1|^1.5 + 0.25*exp(-Vol/40) + |N(0, 0.006)|, 0.002, 0.60).
- Observed IV: sigma_obs = sigma_true + N(0, 0.30 * RelSpread) (quote noise scaled by spread).

## Arm B — activity clocks (paper Finding 5 protocol)

- S = 320 sessions x 390 one-minute bars, seed 20261104. Minute log-returns:
  r = s(k) * sigma_day * eps, eps ~ standardized t_5; s(k) U-shape
  s(k) = 1 + 0.85*exp(-k/55) + 0.85*exp(-(390-k)/55), normalized to mean 1;
  log sigma_day AR(1) phi 0.90 sd 0.28 around daily sd 0.011; jumps: with prob 0.004 per
  minute add N(0, 4*sigma_day*s(k)); price level expansion: deterministic daily log-drift
  log(8)/320 (8x start-to-end) plus cumulative returns.
- Minute volume: V = Vday_t * s(k)^1.4 * exp(0.9*|r|/(s(k)*sigma_day)) * exp(N(0,0.55)),
  Vday_t lognormal around 3.0e7 shares with slow drift.
- Bar types: time bars (9 contiguous blocks/session); diurnally standardised time bars
  (minute returns divided by trailing-60-session per-minute mean |r| scale, then same
  9 blocks, returns re-scaled by the session's mean scale so units stay comparable);
  static volume / dollar bars (thresholds fixed from sessions 1..60 at target 8.75
  bars/session); rolling volume / dollar bars (threshold = trailing-60-session mean daily
  volume / 8.75, causal).
- Metrics: bars/session; excess kurtosis (Fisher) of bar returns, pooled, full and
  "interior" (excluding first and last bar of each session); paired session-level kurtosis
  contrasts vs diurnal bars; lag-1 autocorrelation of squared bar returns (pooled);
  next-bar directional accuracy under previous-bar-sign rule. Ordering also checked on the
  final 40% of sessions (holdout).

## Deviations from the paper (recorded, not hidden)

1. R = 25 draws/day (paper R = 3): reduces Monte Carlo noise symmetrically across designs.
2. Synthetic populations replace the NVDA corpora (per plan; ground truth known exactly).
   Magnitudes are NOT expected to match the paper; the pre-registered claim is the ordering.
3. OptionsDX corpus arm: attempted only if obtainable under the free EOD tier without
   payment; otherwise skipped with the deviation recorded (stop condition 3).
4. Arm B diurnal standardisation uses a trailing-60-session causal scale (paper's exact
   standardisation window is not printed); bar target 8.75/session follows the paper's
   reported ~8.5-9.0 bars/session for rolling clocks.

## Revision log

- 2026-11-03 Arm B v1 DISCARDED as an invalid population (results kept as
  activity-clocks/results_v1_invalid.json). Two population-validity failures, both
  measurable without reference to any clock comparison:
  (1) the frozen volume coupling exp(0.9*|r|/(seas*sigma_day)) with t5 shocks produced
  daily-volume mean/median = 4.5 and max/median = 540 (jump minutes explode volume),
  so trailing-mean thresholds starved typical sessions (rolling clocks realised ~4.0
  bars/session instead of the ~8.75 the protocol targets) — not NVDA-like;
  (2) raw time bars' own squared-return lag-1 autocorrelation was NEGATIVE (-0.125):
  the frozen process (daily-level vol only) contains no intraday volatility clustering,
  so the pre-registered sub-claim "clocks do not remove clustering" had no phenomenon
  to test.
  Arm B v2 changes ONLY the population, minimally: volume coupling capped at
  exp(0.9*min(|z|,3)); minute returns get a GARCH(1,1) (alpha 0.06, beta 0.92) variance
  recursion around sigma_day^2 so clustering exists at bar scale. All clock definitions,
  thresholds, metrics and the target 8.75 bars/session are unchanged. Arm A is untouched.
