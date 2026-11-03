# Claim status table — after the bounded first-party test (2026-11-03)

Verdicts are bounded to our synthetic populations, our parameterisation, and this single
run. Paper numbers remain author-reported. Detail: `test-receipt.md`.

| Claim | Subject | First-party outcome |
|---|---|---|
| iv-c1 | Data & design of the paper (NVDA panel, three layers) | NOT_TESTED — design facts used as population-model inputs only |
| iv-c2 | Plug-in EqCell/Neyman beat SRS on the EW target at all α, 100% coverage | **REPRODUCED** — EqCell 0.73/0.68/0.59/0.45, Neyman 0.82/0.83/0.78/0.72 (CIs exclude 1); coverage 100% at all α; α-gradient matches the paper |
| iv-c3 | PPS: big win on matched LW target "by construction"; 2.47–3.90× penalty on EW | **PARTIAL** — EW penalty reproduced in direction (1.66–2.03×); PPS beats SRS on LW (0.50–0.81) but is NOT best on LW in our population (EqCell lower at all α) → matched dominance is population-dependent, see iv-c14 |
| iv-c4 | Longitudinal tail capture 81.2%/73.7% vs 59.9%; Kish DEFF bounded | NOT_TESTED — longitudinal arm out of pre-registered scope |
| iv-c5 | TOST equivalence at α=0.60; incremental gains over SRS not established | NOT_TESTED — LSTM stack out of scope (separate costing decision) |
| iv-c6 | Prices unforecastable; HAR-IV +21.0%, LSTM +17.2% descriptive IV skill | NOT_TESTED — forecasting arm out of scope |
| iv-c7 | IV skill concentrated in top-5 sessions; clustered DM insignificant | NOT_TESTED — depends on iv-c6 arm |
| iv-c8 | Feature tiers; OPRA.PILLAR rebuild removes 75-DTE truncation | NOT_TESTED — out of scope / commercial data |
| iv-c9 | Rolling activity clocks: stable bar rates, lower kurtosis, clustering stays, no directional alpha | **REPRODUCED_DIRECTION** — bar rates 9.40 (vol) / 11.28 (dol) vs static-dollar blow-up 30.41; pooled interior kurtosis 0.69/0.55 vs 8.73 (time) / 6.83 (diurnal), holdout preserves ordering; pooled squared-AC1 positive under all clocks (0.05–0.18); accuracy 0.493–0.510. Caveats: dollar bar-rate drift; session-level paired Δκ mixed (vol −0.13 p=0.004; dol +0.13 p=0.018) |
| iv-c10 | No public code; data/scripts on request under vendor licences | CONFIRMED_AS_STATED — clean-room reimplementation from the printed specification was feasible; OptionsDX corpus sits behind a store account/checkout flow (not exercised) |
| iv-c11 | Headline arithmetic internally consistent | CONFIRMED (research stage, unchanged) |
| iv-c12 | Bounded feasibility route exists | EXECUTED for both synthetic arms; corpus route not exercised (deviation D3) |
| iv-c13 | NEW first-party: plug-in allocations + coverage on synthetic ground truth | Established by Arm A (see test-receipt) |
| iv-c14 | NEW first-party: PPS matched-target dominance is population-dependent | Established by Arm A, bounded to our population; robustness: LW ordering persists under spread-independent constant noise (EqCell 0.35-0.52 vs PPS 0.51-0.86) |
| iv-c15 | NEW first-party: clock ordering + clustering persistence on synthetic GARCH process | Established by Arm B v2 (see test-receipt) |

Composite: **PARTIAL** (headline alignment reproduced; LW-dominance sub-claim not
reproduced as stated; clock claim reproduced in direction with caveats).
