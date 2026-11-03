"""Arm B v2 — activity-clock audit on a synthetic intraday process.

Population revised from v1 for validity failures recorded in ../PROTOCOL.md
(volume explosion; no intraday clustering). Clock protocol unchanged.

Process and clock protocol frozen in ../PROTOCOL.md before this run.
Clocks: time bars, diurnally standardised time bars, static volume/dollar bars,
rolling (trailing-60-session) volume/dollar bars.
Metrics: bars/session, excess kurtosis (full + interior), lag-1 autocorr of
squared bar returns, next-bar directional accuracy (previous-bar-sign rule).
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 20261104
S = 320
MINS = 390
TARGET_BARS = 8.75
WARM = 60  # trailing window for rolling thresholds / diurnal scale

rng = np.random.default_rng(SEED)


def seasonal(k):
    s = 1 + 0.85 * np.exp(-k / 55.0) + 0.85 * np.exp(-(MINS - k) / 55.0)
    return s / s.mean()


def simulate(rng):
    k = np.arange(MINS)
    seas = seasonal(k)
    log_sig = np.log(0.011)
    drift = np.log(8.0) / S
    rets = np.zeros((S, MINS))
    vols = np.zeros((S, MINS))
    price = np.zeros((S, MINS))
    logp = np.log(100.0)
    for t in range(S):
        log_sig = np.log(0.011) + 0.90 * (log_sig - np.log(0.011)) + rng.normal(0, 0.0031)
        sig_day = np.exp(log_sig)
        eps = rng.standard_t(5, MINS) / np.sqrt(5 / 3)
        # GARCH(1,1) minute variance around sig_day^2 (v2: intraday clustering)
        h = np.empty(MINS)
        hk = sig_day ** 2
        r = np.empty(MINS)
        for kk in range(MINS):
            r[kk] = seas[kk] * np.sqrt(hk) * eps[kk]
            hk = sig_day ** 2 * (1 - 0.06 - 0.92) + 0.06 * (r[kk] / seas[kk]) ** 2 + 0.92 * hk
            h[kk] = hk
        jump = rng.random(MINS) < 0.004
        r = r + jump * rng.normal(0, 4 * sig_day * seas)
        z = np.abs(r) / (seas * sig_day)
        vday = np.exp(rng.normal(np.log(3.0e7), 0.25))
        v = vday / MINS * seas ** 1.4 * np.exp(0.9 * np.minimum(z, 3.0)) * np.exp(rng.normal(0, 0.55, MINS))
        logp += drift
        rets[t] = r
        vols[t] = v
        price[t] = np.exp(logp + np.cumsum(r))
    return rets, vols, price


def excess_kurt(x):
    x = np.asarray(x, dtype=float)
    if len(x) < 4:
        return np.nan
    z = (x - x.mean()) / x.std(ddof=1)
    return float(np.mean(z ** 4) - 3.0)


def agg_bars_from_threshold(cum_series, threshold):
    """Split one session's cumulative series into bars; return bar boundaries (indices)."""
    bounds = []
    acc_start = 0.0
    total = cum_series[-1]
    target = threshold
    idx = np.searchsorted(cum_series, np.arange(threshold, total, threshold))
    return idx  # end-exclusive minute indices where cumulative crosses each multiple


def session_bars(rets_t, vols_t, price_t, kind, thr_v, thr_d, diurnal_scale):
    """Return array of bar log-returns for one session under the given clock."""
    if kind == "time":
        edges = np.linspace(0, MINS, 10).astype(int)
        return np.array([rets_t[edges[i]:edges[i + 1]].sum() for i in range(9)])
    if kind == "diurnal":
        adj = rets_t / diurnal_scale
        scale_back = np.mean(diurnal_scale)
        edges = np.linspace(0, MINS, 10).astype(int)
        return np.array([adj[edges[i]:edges[i + 1]].sum() * scale_back for i in range(9)])
    if kind in ("vol_static", "vol_roll"):
        series = np.cumsum(vols_t)
        thr = thr_v
    else:  # dollar bars
        series = np.cumsum(vols_t * price_t)
        thr = thr_d
    idx = agg_bars_from_threshold(series, thr)
    bounds = np.concatenate([[0], idx, [MINS]])
    out = []
    for i in range(len(bounds) - 1):
        seg = rets_t[bounds[i]:bounds[i + 1]]
        if len(seg) > 0:
            out.append(seg.sum())
    return np.array(out)


def evaluate(rets, vols, price):
    kinds = ["time", "diurnal", "vol_static", "vol_roll", "dol_static", "dol_roll"]
    daily_vol = vols.sum(axis=1)
    daily_dol = (vols * price).sum(axis=1)
    # static thresholds from first WARM sessions
    thr_v_static = daily_vol[:WARM].mean() / TARGET_BARS
    thr_d_static = daily_dol[:WARM].mean() / TARGET_BARS
    # diurnal scale: trailing-60 mean |r| per minute, causal; init from first WARM
    results = {k: {"bars_per_session": [], "sess_kurt_interior": [], "sess_kurt_full": []}
               for k in kinds}
    pooled = {k: [] for k in kinds}          # (session, bar_return) for interior pooled kurt
    pooled_sq = {k: [] for k in kinds}       # ordered bar returns per session for autocorr/accuracy
    for t in range(WARM, S):
        thr_v_roll = daily_vol[t - WARM:t].mean() / TARGET_BARS
        thr_d_roll = daily_dol[t - WARM:t].mean() / TARGET_BARS
        scale = np.mean(np.abs(rets[t - WARM:t]), axis=0)
        scale = scale / scale.mean()
        for kind in kinds:
            if kind == "vol_static":
                bars = session_bars(rets[t], vols[t], price[t], kind, thr_v_static, None, None)
            elif kind == "vol_roll":
                bars = session_bars(rets[t], vols[t], price[t], kind, thr_v_roll, None, None)
            elif kind == "dol_static":
                bars = session_bars(rets[t], vols[t], price[t], kind, None, thr_d_static, None)
            elif kind == "dol_roll":
                bars = session_bars(rets[t], vols[t], price[t], kind, None, thr_d_roll, None)
            elif kind == "diurnal":
                bars = session_bars(rets[t], vols[t], price[t], kind, None, None, scale)
            else:
                bars = session_bars(rets[t], vols[t], price[t], kind, None, None, None)
            results[kind]["bars_per_session"].append(len(bars))
            results[kind]["sess_kurt_full"].append(excess_kurt(bars))
            interior = bars[1:-1] if len(bars) > 4 else bars
            results[kind]["sess_kurt_interior"].append(excess_kurt(interior))
            pooled[kind].append((t, interior))
            pooled_sq[kind].append(bars)
    summary = {}
    holdout_from = WARM + int(0.6 * (S - WARM))
    for kind in kinds:
        all_int = np.concatenate([b for _, b in pooled[kind]])
        ho_int = np.concatenate([b for tt, b in pooled[kind] if tt >= holdout_from])
        bars_all = pooled_sq[kind]
        # pooled lag-1 autocorr of squared returns (within session, concatenated pairs)
        sq_all = []
        pairs = []
        pair_x, pair_y = [], []
        for b in bars_all:
            sq = b ** 2
            sq_all.append(sq)
            if len(sq) > 1:
                pairs.append(np.corrcoef(sq[:-1], sq[1:])[0, 1])
                pair_x.append(sq[:-1]); pair_y.append(sq[1:])
        pooled_ac1 = float(np.corrcoef(np.concatenate(pair_x), np.concatenate(pair_y))[0, 1]) if pair_x else float('nan')
        # directional accuracy: predict next bar sign = previous bar sign
        hits, tot = 0, 0
        for b in bars_all:
            if len(b) > 1:
                pred = np.sign(b[:-1])
                act = np.sign(b[1:])
                hits += int(np.sum((pred == act) & (act != 0)))
                tot += int(np.sum(act != 0))
        summary[kind] = {
            "bars_per_session_mean": round(float(np.mean(results[kind]["bars_per_session"])), 2),
            "bars_per_session_sd": round(float(np.std(results[kind]["bars_per_session"])), 2),
            "kurt_interior_pooled": round(excess_kurt(all_int), 2),
            "kurt_interior_holdout": round(excess_kurt(ho_int), 2),
            "kurt_full_pooled": round(excess_kurt(np.concatenate(bars_all)), 2),
            "sess_kurt_interior_mean": round(float(np.nanmean(results[kind]["sess_kurt_interior"])), 2),
            "sqret_ac1_mean_of_sessions": round(float(np.nanmean(pairs)), 3),
            "sqret_ac1_pooled": round(pooled_ac1, 3),
            "next_bar_accuracy_prevsign": round(hits / tot, 4) if tot else None,
        }
    # paired session-level kurtosis contrasts vs diurnal (interior)
    contrasts = {}
    for kind in ("vol_roll", "dol_roll", "time"):
        a = np.array(results[kind]["sess_kurt_interior"])
        b = np.array(results["diurnal"]["sess_kurt_interior"])
        d = a - b
        d = d[~np.isnan(d)]
        from scipy import stats
        tt = stats.ttest_1samp(d, 0.0)
        contrasts[f"{kind}_minus_diurnal"] = {
            "mean_delta_kurt": round(float(d.mean()), 2),
            "t": round(float(tt.statistic), 2), "p": float(tt.pvalue)}
    np.savez("session_data.npz",
             **{f"pooled_{k}": np.array([len(b) for _, b in pooled[k]]) for k in kinds},
             **{f"bars_{k}": np.array(results[k]["bars_per_session"]) for k in kinds},
             **{f"skurt_{k}": np.array(results[k]["sess_kurt_interior"]) for k in kinds})
    import pickle
    with open("pooled_returns.pkl", "wb") as fh:
        pickle.dump({k: [b for _, b in pooled[k]] for k in kinds}, fh)
    return summary, contrasts


if __name__ == "__main__":
    rets, vols, price = simulate(rng)
    summary, contrasts = evaluate(rets, vols, price)
    out = {"seed": SEED, "sessions_total": S, "sessions_scored": S - WARM,
           "price_expansion_start_to_end": round(float(price[-1, -1] / price[0, 0]), 1),
           "summary": summary, "paired_contrasts_interior_kurt": contrasts}
    print(json.dumps(out, indent=2))
    with open("results_check.json", "w") as f:
        json.dump(out, f, indent=2)
    # kurtosis chart (proof target)
    labels = ["time", "diurnal", "vol_static", "vol_roll", "dol_static", "dol_roll"]
    vals = [summary[k]["kurt_interior_pooled"] for k in labels]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    colors = ["#888", "#555", "#c9a227", "#1f77b4", "#c97b27", "#2ca02c"]
    ax.bar(labels, vals, color=colors)
    ax.set_ylabel("Interior excess kurtosis (pooled)")
    ax.set_title("Activity clocks vs time clocks — synthetic intraday process (Arm B)")
    for i, v in enumerate(vals):
        ax.text(i, v + 0.08, f"{v:.2f}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig("kurtosis-chart.png", dpi=150)
    print("chart saved")
