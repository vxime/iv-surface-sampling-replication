"""Per-cell decomposition diagnostic for Arm A (public replication package).

For alpha in {0.25, 0.60} and the PPS / EqCell designs, reports per grid cell:
the mean number of draws per replication, and the cell's liquidity-weighted
(LW) RMSE in bps against the full-frame benchmark. Mirrors arm_a.run()'s
sampling exactly (same population seed path, same estimators, same imputation).
Summary values reproduce results/percell_decomposition.txt.
"""
import numpy as np, csv
import arm_a as A

def run(alphas=(0.25, 0.60), designs=("PPS", "EqCell")):
    rng = np.random.default_rng(A.SEED)
    days = A.gen_population(rng)
    rows = []
    for alpha in alphas:
        draws = {d: np.zeros((len(days), A.H)) for d in designs}
        sqerr = {d: np.zeros((len(days), A.H)) for d in designs}
        for t, day in enumerate(days):
            cell, sig, w, N = day["cell"], day["sig"], day["w"], day["N"]
            counts = np.array([(cell == h).sum() for h in range(A.H)])
            present = np.where(counts > 0)[0]
            bench_lw = np.array([np.sum(w[cell == h] * sig[cell == h]) / np.sum(w[cell == h])
                                 for h in range(A.H)])
            n = int(round(alpha * N))
            alloc_eq = A.waterfill_alloc(day["lag_sd"].copy(), counts, n)
            pi_pps = A.pps_pis(w, n)
            for r in range(A.R_DRAWS):
                samples = {}
                samples["PPS"] = A.madow_sample(pi_pps, n, rng), None
                idx_pps = samples["PPS"][0]
                samples["PPS"] = (idx_pps, pi_pps[idx_pps])
                idx_parts, pi_parts = [], []
                for h in range(A.H):
                    members = np.where(cell == h)[0]
                    if len(members) == 0:
                        continue
                    nh = min(alloc_eq[h], len(members))
                    if nh > 0:
                        chosen = rng.choice(members, nh, replace=False)
                        idx_parts.append(chosen)
                        pi_parts.append(np.full(nh, nh / len(members)))
                samples["EqCell"] = (np.concatenate(idx_parts), np.concatenate(pi_parts))
                for dname in designs:
                    idx, pi_s = samples[dname]
                    cs = cell[idx]
                    _, lw = A.hajek_cell_est(sig[idx], pi_s, cs, w[idx], present)
                    for h in range(A.H):
                        draws[dname][t, h] += (cs == h).sum() / A.R_DRAWS
                        sqerr[dname][t, h] += (lw[h] - bench_lw[h]) ** 2 / A.R_DRAWS
        for dname in designs:
            md = draws[dname].mean(axis=0)
            rmse = np.sqrt(sqerr[dname].mean(axis=0)) * 1e4
            for h in range(A.H):
                rows.append({"alpha": alpha, "design": dname, "cell": h + 1,
                             "mean_draws": round(float(md[h]), 1),
                             "lw_rmse_bps": round(float(rmse[h]))})
    return rows

if __name__ == "__main__":
    rows = run()
    with open("percell.csv", "w", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=["alpha", "design", "cell", "mean_draws", "lw_rmse_bps"])
        wtr.writeheader(); wtr.writerows(rows)
    for alpha in (0.25, 0.60):
        for dname in ("PPS", "EqCell"):
            sel = [r for r in rows if r["alpha"] == alpha and r["design"] == dname]
            thin = min(sel, key=lambda r: r["mean_draws"]); fat = max(sel, key=lambda r: r["mean_draws"])
            print(f"alpha={alpha} {dname}: draws min {min(r['mean_draws'] for r in sel)} median "
                  f"{sorted(r['mean_draws'] for r in sel)[6]} max {max(r['mean_draws'] for r in sel)}; "
                  f"thinnest cell{thin['cell']} {thin['mean_draws']} draws -> LW RMSE {thin['lw_rmse_bps']} bps; "
                  f"fattest cell{fat['cell']} {fat['mean_draws']} -> {fat['lw_rmse_bps']} bps")
