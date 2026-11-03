"""Arm A — design-target alignment audit on a synthetic option-chain population.

Clean-room reimplementation of the sampling protocol printed in
Bastola & Prushansky (arXiv:2610.33438), sections 3.1-3.2.
Population parameters frozen in ../PROTOCOL.md before this run.
"""
import json
import numpy as np

SEED = 20261103
T_DAYS = 200
R_DRAWS = 25
ALPHAS = [0.25, 0.40, 0.60, 0.80]
M_EDGES = [0.60, 0.90, 1.00, 1.10, 1.40]
TAU_EDGES = [7, 30, 90, 366]
H = 12

rng = np.random.default_rng(SEED)


def gen_population(rng):
    days = []
    L = 0.34
    prev_cell_sd = None
    for t in range(T_DAYS):
        L = 0.34 + 0.85 * (L - 0.34) + rng.normal(0, 0.045)
        a = rng.normal(-0.55, 0.10)
        b = rng.normal(1.6, 0.35)
        d = rng.normal(-0.05, 0.015)
        N = int(np.clip(round(np.exp(rng.normal(np.log(550), 0.35))), 300, 900))
        m = np.clip(1 + 0.115 * rng.standard_t(4, N), 0.60, 1.399)
        dte = np.clip(np.round(np.exp(rng.normal(np.log(48), 0.75, N))), 7, 365)
        sig_true = L + a * (m - 1) + b * (m - 1) ** 2 + d * (1 - np.exp(-dte / 90.0))
        sig_true = np.clip(sig_true, 0.05, 3.00)
        logvol = rng.normal(2.6 - 3.2 * np.abs(m - 1) - 0.004 * dte, 0.95)
        vol = np.exp(logvol)
        relspread = np.clip(
            0.012 + 0.30 * np.abs(m - 1) ** 1.5 + 0.25 * np.exp(-vol / 40.0)
            + np.abs(rng.normal(0, 0.006, N)),
            0.002, 0.60)
        sig_obs = sig_true + rng.normal(0, 0.30 * relspread)
        w = (vol + 1.0) / (relspread + 1e-4)
        cell = (np.digitize(m, M_EDGES) - 1) * 3 + (np.digitize(dte, TAU_EDGES) - 1)
        # lagged plug-in dispersion: prior day's within-cell sd of observed IV
        if prev_cell_sd is None:
            sds = np.array([sig_obs[cell == h].std(ddof=1) if (cell == h).sum() > 1 else np.nan
                            for h in range(H)])
            lag_sd = np.full(H, np.nanmean(sds))
        else:
            lag_sd = prev_cell_sd
        cur = np.array([sig_obs[cell == h].std(ddof=1) if (cell == h).sum() > 1 else np.nan
                        for h in range(H)])
        fill = np.nanmean(cur)
        prev_cell_sd = np.where(np.isnan(cur), fill, cur)
        days.append(dict(N=N, cell=cell, sig=sig_obs, w=w, lag_sd=lag_sd))
    return days


def waterfill_alloc(weights, caps, total):
    """Bounded allocation: 1 <= n_h <= cap_h, sum = total (water-filling + largest remainder)."""
    Hh = len(weights)
    n = np.ones(Hh, dtype=float)
    caps = caps.astype(float)
    remaining = total - Hh
    active = caps > 1
    w = np.where(weights > 0, weights, 0.0)
    while remaining > 1e-9 and active.any():
        wa = np.where(active, w, 0.0)
        if wa.sum() <= 0:
            wa = np.where(active, 1.0, 0.0)
        share = remaining * wa / wa.sum()
        room = np.where(active, caps - n, 0.0)
        add = np.minimum(share, room)
        n += add
        remaining -= add.sum()
        active = n < caps - 1e-9
        if add.sum() <= 1e-9:
            break
    # largest-remainder rounding to integers with exact total
    base = np.floor(n).astype(int)
    base = np.minimum(base, caps.astype(int))
    base = np.maximum(base, 1)
    diff = total - base.sum()
    frac = n - np.floor(n)
    order = np.argsort(-frac)
    i = 0
    while diff > 0 and i < 10 * Hh:
        h = order[i % Hh]
        if base[h] < caps[h]:
            base[h] += 1
            diff -= 1
        i += 1
    i = 0
    while diff < 0 and i < 10 * Hh:
        h = order[-(i % Hh) - 1]
        if base[h] > 1:
            base[h] -= 1
            diff += 1
        i += 1
    return base


def pps_pis(sizes, n):
    """Inclusion probabilities pi = min(1, c*M) via iterative certainty capping."""
    M = sizes.astype(float)
    pi = np.zeros_like(M)
    free = np.ones(len(M), dtype=bool)
    budget = n
    for _ in range(len(M) + 1):
        if budget <= 0 or not free.any():
            break
        c = budget / M[free].sum()
        cand = c * M[free]
        over = cand >= 1.0
        if not over.any():
            pi[free] = cand
            budget = 0
            break
        idx = np.where(free)[0][over]
        pi[idx] = 1.0
        budget -= len(idx)
        free[idx] = False
    return pi


def madow_sample(pi, n, rng):
    """Madow single-start systematic PPS on a randomly permuted frame."""
    N = len(pi)
    perm = rng.permutation(N)
    cum = np.cumsum(pi[perm])
    start = rng.uniform(0, 1)
    points = start + np.arange(n)
    pos = np.searchsorted(cum, points, side="left")
    pos = pos[pos < N]
    return perm[pos]


def hajek_cell_est(sig_s, pi_s, cell_s, w_s, present):
    """Per-cell Hajek (EW) and HT-ratio (LW) estimates with paper's empty-cell imputation."""
    ew = np.full(H, np.nan)
    lw = np.full(H, np.nan)
    inv = 1.0 / pi_s
    for h in present:
        sel = cell_s == h
        if sel.any():
            ew[h] = np.sum(sig_s[sel] * inv[sel]) / np.sum(inv[sel])
            lw[h] = np.sum(w_s[sel] * sig_s[sel] * inv[sel]) / np.sum(w_s[sel] * inv[sel])
    # global design-weighted means for imputation
    g_ew = np.sum(sig_s * inv) / np.sum(inv)
    g_lw = np.sum(w_s * sig_s * inv) / np.sum(w_s * inv)
    ew = np.where(np.isnan(ew), g_ew, ew)
    lw = np.where(np.isnan(lw), g_lw, lw)
    return ew, lw


def run():
    days = gen_population(rng)
    # per-day mean-over-draws RMSE [day][alpha][design][target]
    designs = ["SRS", "Neyman", "EqCell", "PPS"]
    targets = ["EW", "LW"]
    day_rmse = np.zeros((T_DAYS, len(ALPHAS), len(designs), len(targets)))
    coverage = np.zeros((len(ALPHAS), len(designs)))  # mean fraction of present cells hit
    
    for t, day in enumerate(days):
        cell, sig, w, N = day["cell"], day["sig"], day["w"], day["N"]
        counts = np.array([(cell == h).sum() for h in range(H)])
        present = np.where(counts > 0)[0]
        bench_ew = np.array([sig[cell == h].mean() for h in present])
        bench_lw = np.array([np.sum(w[cell == h] * sig[cell == h]) / np.sum(w[cell == h])
                             for h in present])
        for ai, alpha in enumerate(ALPHAS):
            n = int(round(alpha * N))
            allocs = {
                "Neyman": waterfill_alloc(counts * day["lag_sd"], counts, n),
                "EqCell": waterfill_alloc(day["lag_sd"].copy(), counts, n),
            }
            pi_pps = pps_pis(w, n)
            for r in range(R_DRAWS):
                samples = {}
                samples["SRS"] = (rng.choice(N, n, replace=False), np.full(n, n / N))
                pps_idx = madow_sample(pi_pps, n, rng)
                samples["PPS"] = (pps_idx, pi_pps[pps_idx])
                for dname in ("Neyman", "EqCell"):
                    idx_parts, pi_parts = [], []
                    for h in range(H):
                        members = np.where(cell == h)[0]
                        if len(members) == 0:
                            continue
                        nh = min(allocs[dname][h], len(members))
                        if nh > 0:
                            chosen = rng.choice(members, nh, replace=False)
                            idx_parts.append(chosen)
                            pi_parts.append(np.full(nh, nh / len(members)))
                    idx = np.concatenate(idx_parts)
                    samples[dname] = (idx, np.concatenate(pi_parts))
                for di, dname in enumerate(designs):
                    idx, pi_s = samples[dname]
                    cs = cell[idx]
                    hit = len(np.unique(cs[np.isin(cs, present)]))
                    if r == 0:
                        coverage[ai, di] += hit / len(present)
                    ew, lw = hajek_cell_est(sig[idx], pi_s, cs, w[idx], present)
                    day_rmse[t, ai, di, 0] += np.sqrt(np.mean((ew[present] - bench_ew) ** 2)) / R_DRAWS
                    day_rmse[t, ai, di, 1] += np.sqrt(np.mean((lw[present] - bench_lw) ** 2)) / R_DRAWS

    coverage = coverage / T_DAYS  # accumulated once per day (first draw) -> mean daily fraction
    pooled = day_rmse.mean(axis=0)  # [alpha][design][target], in IV units
    # whole-day cluster bootstrap for ratios vs SRS
    boot_rng = np.random.default_rng(777)
    B = 1000
    ratios = np.zeros((len(ALPHAS), len(designs), len(targets)))
    ci = np.zeros((len(ALPHAS), len(designs), len(targets), 2))
    for ai in range(len(ALPHAS)):
        for ti in range(len(targets)):
            base = pooled[ai, 0, ti]
            for di in range(len(designs)):
                ratios[ai, di, ti] = pooled[ai, di, ti] / base
            boot = np.zeros((B, len(designs)))
            for b in range(B):
                didx = boot_rng.integers(0, T_DAYS, T_DAYS)
                bm = day_rmse[didx, ai, :, ti].mean(axis=0)
                boot[b] = bm / bm[0]
            for di in range(len(designs)):
                ci[ai, di, ti] = np.percentile(boot[:, di], [2.5, 97.5])
    out = {"seed": SEED, "days": T_DAYS, "draws_per_day": R_DRAWS,
           "alphas": ALPHAS, "designs": designs, "targets": targets,
           "rmse_bps": {}, "ratio_vs_srs": {}, "coverage_frac_first_draw": {}}
    for ai, alpha in enumerate(ALPHAS):
        out["rmse_bps"][str(alpha)] = {
            targets[ti]: {designs[di]: round(float(pooled[ai, di, ti]) * 1e4, 1)
                          for di in range(len(designs))} for ti in range(2)}
        out["ratio_vs_srs"][str(alpha)] = {
            targets[ti]: {designs[di]: {"ratio": round(float(ratios[ai, di, ti]), 3),
                                        "ci95": [round(float(ci[ai, di, ti, 0]), 3),
                                                 round(float(ci[ai, di, ti, 1]), 3)]}
                          for di in range(len(designs))} for ti in range(2)}
        out["coverage_frac_first_draw"][str(alpha)] = {
            designs[di]: round(float(coverage[ai, di]), 4) for di in range(len(designs))}
    return out, days


if __name__ == "__main__":
    out, days = run()
    Ns = [d["N"] for d in days]
    out["population"] = {"contracts_total": int(sum(Ns)), "contracts_per_day_median": float(np.median(Ns))}
    print(json.dumps(out, indent=2))
    with open("results.json", "w") as f:
        json.dump(out, f, indent=2)
