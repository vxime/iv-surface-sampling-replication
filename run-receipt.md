Public edition of the test receipt from the private research dossier (AI Token Content Lab). No content removed; this topic involved no third-party accounts, gateways or credentials.

# Test receipt — bounded first-party audit of arXiv:2610.33438

Topic: `2026-11-03-iv-surface-sampling-clocks` · Stage: TESTING → TESTING_COMPLETE
Run date: 2026-11-03 (assistant sandbox; no paid data, no accounts, no external model calls)
Scope: the pre-registered plan in `experiment-plan.md` — Arm A (surface sampling, synthetic
population with known truth), Arm B (activity clocks, synthetic intraday process), optional
OptionsDX corpus arm. The LSTM equivalence stack was out of scope by pre-registration.

## Composite verdict: PARTIAL

The paper's two falsifiable cores were tested on synthetic populations where ground truth
is known exactly. The design–target alignment headline reproduces on the equal-weighted
side in full; its liquidity-weighted sub-claim does not reproduce as stated. The
activity-clock claim reproduces in direction on every headline metric, with two recorded
caveats. All verdicts are bounded to our synthetic populations, our parameterisation and
this single run; magnitudes were pre-registered as not claimed.

## Arm A — surface sampling (200 days, 111,573 contracts, median 534/day, R=25 draws/day)

Protocol implemented verbatim from the paper (§3.1–3.2): 4×3 grid, lagged plug-in
dispersion, water-filling allocations, Madow systematic PPS with certainty capping,
Hájek (EW) / HT-ratio (LW) estimators, paper's empty-cell imputation, pooled RMSE as the
mean of daily RMSE, 1,000-replicate whole-day cluster bootstrap. Full table:
`experiments/surface-sampling/ratio-table.md`, raw output `results.json`.

- **EW target — REPRODUCED.** Equal-cell ratios vs SRS: 0.73 / 0.68 / 0.59 / 0.45 at
  α = 0.25 / 0.40 / 0.60 / 0.80; Neyman: 0.82 / 0.83 / 0.78 / 0.72. All bootstrap CIs
  exclude 1; ordering EqCell < Neyman < SRS holds at every α; the plug-in advantage grows
  with α, matching the paper's gradient (paper: EqCell 0.68 → 0.47). Stratum coverage of
  both plug-in designs: 100% at every α (SRS 99.7%, PPS 98.9% at α=0.25).
- **Mismatch penalty — REPRODUCED in direction.** Liquidity PPS applied to the EW target
  inflates RMSE 1.66× / 1.84× / 1.96× / 2.03× (paper: 2.47–3.90× on NVDA). Same sign,
  clear multiple, smaller magnitude on our population.
- **Matched-target dominance — NOT REPRODUCED as stated.** PPS does beat SRS on the LW
  target at every α (0.81 / 0.74 / 0.61 / 0.50), but it is not the best design there:
  equal-cell is lower at every α (0.72 / 0.67 / 0.57 / 0.42), Neyman second. In the paper's
  NVDA corpus PPS reaches 0.05 at α=0.80 — an order of magnitude beyond anything here.
  Reading: the "wins by construction" property holds for the *pooled* functional the
  weights define, but the paper's target is a grid of *per-cell* LW means; when the
  liquidity score does not also track within-cell precision, PPS starves low-liquidity
  cells and stratified coverage wins. The dominance is a property of the NVDA corpus's
  joint distribution of volume, spread and noise — not a construction guarantee.
  This is the audit's main new finding and is stated bounded to our population (iv-c14).

## Arm B — activity clocks (320 sessions × 390 minutes; scored on trailing-60 protocol, 260 sessions)

Population v2 (v1 discarded for validity failures, see D2): U-shaped seasonality,
GARCH(1,1) minute variance (minute-level squared-return AC1 +0.068 — clustering present),
t5 shocks, jumps, 8.6× start-to-end price expansion, daily-volume mean/median 1.07.

- **Bar-rate stability — REPRODUCED with a dollar caveat.** Rolling volume bars:
  9.40 ± 3.20 bars/session against the 8.75 target (paper: ~8.5–9.0). Rolling dollar
  bars: 11.28 ± 4.67 — the trailing window lags the 8.6× expansion, but static dollar
  bars blow up to 30.41 ± 18.29 and static volume drifts to 10.27 ± 3.45, so the causal
  recalibration is doing the stabilising work the paper claims.
- **Kurtosis ordering — REPRODUCED (pooled, the paper's headline metric).** Interior
  excess kurtosis: rolling volume 0.69, rolling dollar 0.55, static volume 0.46,
  static dollar 1.98 — versus time bars 8.73 and diurnally standardised 6.83. Ordering
  preserved on the holdout (final 40% of sessions: 0.41 / 0.56 vs 12.64 / 8.18).
  Session-level paired contrasts are mixed (volume −0.13, p=0.004, favouring rolling;
  dollar +0.13, p=0.018, favouring diurnal) — per-session kurtosis at ~9 bars is
  small-sample-dominated; recorded as a caveat, not hidden.
- **Clustering not removed — REPRODUCED.** Pooled lag-1 autocorrelation of squared bar
  returns is positive under every clock (time 0.049, diurnal 0.052, vol-static 0.082,
  vol-roll 0.073, dol-static 0.179, dol-roll 0.105); no clock drives it to zero.
- **No directional predictability — REPRODUCED.** Previous-bar-sign accuracy
  0.493–0.510 across all six clocks (paper: 48.6–51.0%).

## Deviations (all recorded, none hidden)

- D1: R=25 Monte Carlo draws/day in Arm A (paper R=3) — pre-registered; reduces MC noise
  symmetrically across designs.
- D2: Arm B v1 population discarded before any verdict (outputs kept as
  `results_v1_invalid.json`): the frozen volume coupling produced daily-volume
  mean/median 4.5 and max/median 540, starving rolling thresholds (~4.0 bars/session);
  and the v1 process contained no intraday clustering (time bars' own squared AC1
  −0.125), so the clustering sub-claim had no phenomenon to test. v2 changed only the
  population, minimally (capped coupling; GARCH), per stop condition 2's recorded-reason
  rule; full log in `experiments/PROTOCOL.md`. Arm A untouched.
- D3: OptionsDX corpus arm SKIPPED. The NVDA EOD corpus sits behind the vendor store's
  account/checkout flow (the product page's free-sample link is a SPY file and returned
  an empty response on 2026-11-03). No account was created and nothing was purchased
  (stop condition 3). Running this arm needs the owner's explicit go-ahead for the
  vendor account, or a data drop from the owner.
- D4: Plan wording slip, substance unaffected: experiment-plan.md said the plug-in
  advantage shows "the gap widening as α falls"; the paper's table and our run both show
  the ratio falling as α *rises*. Corrected here.
- D5: Arm B clustering metric: the session-mean of per-session AC1 estimates carries a
  ≈ −1/(n−1) small-sample bias at ~9 bars/session (all values ≈ −0.1); replaced by the
  pooled within-session AC1, which is the quantity comparable to the paper's ρ₁.
  Both estimators are in `results.json`.
- D6: Absolute magnitudes (RMSE bps, kurtosis levels) differ from the paper's NVDA
  values, as pre-registered: synthetic populations, ordering is the claim.
- D7: The kurtosis chart (`experiments/activity-clocks/kurtosis-chart.png`) is a binary
  artefact and is kept in the local working copy only; the GitHub connector stores text
  only. It joins the blog repository at the publication-preparation stage.

## What was NOT tested (unchanged from pre-registration)

Longitudinal tail-capture and Kish DEFF (iv-c4), TOST equivalence of subsampled LSTM
training (iv-c5), price/IV forecasting and HAR-IV (iv-c6), skill concentration (iv-c7),
feature tiers and the OPRA.PILLAR schema rebuild (iv-c8), and the real NVDA corpora
themselves (iv-c1). These remain author-reported only, and any article text must keep
that attribution.

## Files

- `experiments/PROTOCOL.md` — frozen parameters + revision log
- `experiments/surface-sampling/arm_a.py`, `results.json`, `ratio-table.md`
- `experiments/activity-clocks/arm_b.py` (v1), `arm_b_v2.py`, `results.json` (v2),
  `results_v1_invalid.json`
- `claim-status-table.md` — per-claim outcomes, including new first-party claims
  iv-c13…iv-c15 in `claims.json`
- Evidence pack / reader-handoff assessment are revised at the drafting stage with the
  first-party Brief, per the lab's established flow (the executed-evidence artifacts
  change the derived classification; doing it now, before the Brief's first-party
  revision, would bind the assessment to a Brief that is about to change).

## 审阅补记 (added at the receipt-review stage, 2026-11-03)

Mechanism diagnostic for the Arm A matched-target outcome, computed on the frozen Arm A
population (same seed): the within-cell share of liquidity weight held by the top-5
contracts has median 0.56 (p25 0.46, p75 0.67), and PPS at α=0.60 carries a median of
165 certainty units per day. Weight concentration is therefore present in our population;
the equal-cell advantage on the LW target is more plausibly driven by per-cell sample
starvation under global PPS (thin cells receive few draws, while the target scores every
cell equally) than by an absence of concentration. This is a mechanism reading of our
population, labelled as such wherever the article uses it.


## Review addendum 2 (round 3, 2026-11-03)

A reader-panel reviewer (R5) raised a confound in Arm A: the observation noise is proportional to
the relative spread, while the PPS size variable divides by the same spread, coupling noise to
weights. Per the pre-registered stop rule this was answered with a recorded robustness run, not a
tuning exercise: identical population, protocol and seed path; only the noise term changed to a
spread-independent constant sd of 0.0673 (matched to the baseline population's mean noise sd).
Result (experiments/surface-sampling/results_constnoise.json, runner arm_a_constnoise.py): on the
LW target, PPS ratios 0.86/0.72/0.59/0.51 vs EqCell 0.52/0.47/0.40/0.35 across alpha — the LW
ordering is unchanged, so the coupling does not drive iv-c14. (EW-side ratios shift substantially
under constant noise, as expected when within-cell variance is reshaped; the robustness claim is
scoped to the LW ordering only.)
