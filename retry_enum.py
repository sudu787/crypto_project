"""Item 8: repeated pruned-enumeration attempts (Gama-Nguyen-Regev / Liu-Nguyen 2013 BDD enumeration).

Attempt = BDD enumeration with linear pruning on a re-randomised reduced basis: the target survives iff for every
k = 1..d the squared norm of the projection of o onto the last k Gram-Schmidt directions is at most (k/d) R^2
(Liu-Nguyen 2013, Sec. 4.1 and Alg. 4). That condition is evaluated from the projections, as for Babai; the
enumeration itself is not run (only success matters here, not cost).

Fixed-norm model (Assumption A): with z uniform on the sphere and S_k(z) = sum of z_i^2 over the last k levels,
success iff ||o||^2 <= R^2 * q(z), q(z) = min_k (k/d) / S_k(z). Its law does not depend on the basis profile at all,
so under Assumption A every attempt on an instance has the same success probability G(||o||^2 / R^2).
Independent model (Liu-Nguyen's "success probability multiplied by l"): one probability for every attempt, here the
true mean over the instances (the most favourable version of that model).

Data: the R8 bases (tag 7: BKZ-20 n=95, BKZ-10 n=85; K=64; 16 lattices x 200 targets; eta in {2, 3}). These bases
were used for the Babai test R8; enumeration outcomes on them had not been computed when R12 was fixed.

--choose   model only (no outcomes): mean success for candidate radius factors, to fix R^2 = f * d * sigma^2.

R12 (fixed 8 Nov 2026, before any enumeration outcome was computed). Linear pruning with R^2 = F_R12 * d * sigma^2
    (F_R12 chosen by --choose from the model alone, set below). (a) Independence: the permutation test of R4 (variance
    of per-target success counts, shuffling each basis's success column within its lattice, 10,000 shuffles) rejects
    at p < 0.01 in every (setting, eta) with at least 50 successes. (b) Model: same 16 cells and 99% Wilson
    intervals as R8; the fixed-norm model G is off in at most 2 cells and in fewer than the independent model.
    R12 passes if (a) and (b) both hold. Reported either way.
"""
import argparse
import json
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import retry_exact as X  # noqa: E402
import retry_study as R  # noqa: E402
import toy_lwe_test as T  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
SETS = [(20, 95, 64), (10, 85, 64)]
F_R12 = 1.1  # fixed from --choose (model mean success 15.6-15.8% in all four), before any outcome was computed
rng = np.random.default_rng(12)


def q_samples(d, M=1_000_000):
    out = []
    kk = np.arange(1, d + 1) / d
    for _ in range(M // 20_000):
        z = rng.standard_normal((20_000, d))
        z2 = z * z / (z * z).sum(1, keepdims=True)
        S = np.cumsum(z2[:, ::-1], 1)  # last 1, last 2, ... levels
        out.append((kk[None, :] / S).min(1))
    return np.sort(np.concatenate(out))


def G(qs, t):
    """P(success) for ||o||^2 / R^2 = t."""
    return 1 - np.searchsorted(qs, np.asarray(t, float)) / len(qs)


def choose():
    for beta, n, K in SETS:
        d = 2 * n
        qs = q_samples(d)
        R.TAG = 7
        for eta in R.ETAS:
            r = np.concatenate([(np.concatenate([-s, e], 1) ** 2).sum(1) for s, e, _ in
                                (R.instance_offsets(n, i, eta) for i in range(R.LATTICES))])
            print(f"{T.beta_name(beta)} n={n} eta={eta}: model mean success for R^2 = f d sigma^2: " +
                  "  ".join(f"f={f}: {100 * G(qs, r / (f * d * eta / 2)).mean():.2f}%" for f in (1.0, 1.1, 1.2, 1.3, 1.5)), flush=True)


def wilson(k, n, z=2.5758293035489):
    return X.wilson(k, n, z)


def test(sets=SETS, tag=7, etas=None, label="R12", outfile="retry_enum.json"):
    assert F_R12 is not None
    etas = etas or R.ETAS
    out = {}
    for beta, n, K in sets:
        d = 2 * n
        qs = q_samples(d)
        R.TAG = tag
        offs = {eta: [R.instance_offsets(n, i, eta) for i in range(R.LATTICES)] for eta in etas}
        S = {eta: np.zeros((R.LATTICES, R.TARGETS, K), bool) for eta in etas}
        kk = np.arange(1, d + 1) / d
        for idx in range(R.LATTICES):
            for j in range(K):
                Bs, nrm = T.gso(np.load(X.heldout_path(beta, n, idx, j, tag)))
                U = Bs / np.sqrt(nrm)[:, None]
                Pp, Qp = R.perms(n, idx, j)
                for eta in etas:
                    s, e, _ = offs[eta][idx]
                    o = np.concatenate([-s[:, Pp], e[:, Qp]], 1)
                    c2 = (o @ U.T) ** 2
                    Sk = np.cumsum(c2[:, ::-1], 1)
                    S[eta][idx, :, j] = (Sk <= kk[None, :] * F_R12 * d * eta / 2 + 1e-9).all(1)
            print(f"  {label} {T.beta_name(beta)} n={n} lattice {idx} done", flush=True)
        for eta in etas:
            Sx = S[eta]
            r = np.stack([(np.concatenate([-s, e], 1) ** 2).sum(1) for s, e, _ in offs[eta]])  # (lattice, target)
            g = G(qs, r / (F_R12 * d * eta / 2))
            counts, N = Sx.sum(2), R.LATTICES * R.TARGETS
            stat = counts.var()
            more = 0
            for _ in range(10_000 // 50):
                sh = np.stack([np.take_along_axis(Sx, rng.random(Sx.shape).argsort(1), 1).sum(2) for _ in range(50)])
                more += int((sh.reshape(50, -1).var(1) >= stat).sum())
            p_perm = (more + 1) / 10_001
            pbar = float(g.mean())
            cells = []
            for k in (K // 8, K // 2, K, "never"):
                if k == "never":
                    meas, pf, pi = int((counts == 0).sum()), float(((1 - g) ** K).mean()), (1 - pbar) ** K
                else:
                    meas, pf, pi = int(Sx[:, :, :k].any(2).sum()), float((1 - (1 - g) ** k).mean()), 1 - (1 - pbar) ** k
                lo, hi = wilson(meas, N)
                cells.append({"k": k, "measured": meas / N, "ci": [lo, hi], "fixed_norm": pf, "independent": pi,
                              "fixed_off": not lo <= pf <= hi, "independent_off": not lo <= pi <= hi})
            row = {"mean_success": float(Sx.mean()), "model_mean": pbar, "successes": int(Sx.sum()), "count_var": float(stat),
                   "var_fixed": float((g * (1 - g) * K).mean() + (g * K).var()), "var_independent": K * pbar * (1 - pbar),
                   "perm_p": p_perm, "cells": cells}
            out[f"{beta},{n},{eta}"] = row
            print(f"{T.beta_name(beta)} n={n} eta={eta}: success/attempt {row['mean_success']:.4f} (model {pbar:.4f}); "
                  f"count variance {stat:.2f} (fixed-norm {row['var_fixed']:.2f}, independent {row['var_independent']:.2f}); "
                  f"perm p={p_perm:.4g}", flush=True)
            for c in cells:
                print(f"    k={c['k']!s:>5}: measured {100 * c['measured']:5.1f}% ({100 * c['ci'][0]:.1f}-{100 * c['ci'][1]:.1f})  "
                      f"fixed-norm {100 * c['fixed_norm']:5.1f}%{' OFF' if c['fixed_off'] else ''}  "
                      f"independent {100 * c['independent']:5.1f}%{' OFF' if c['independent_off'] else ''}", flush=True)
    rows = [v for v in out.values()]
    a_ok = all(v["perm_p"] < 0.01 for v in rows if v["successes"] >= 50)
    off_f = sum(c["fixed_off"] for v in rows for c in v["cells"])
    off_i = sum(c["independent_off"] for v in rows for c in v["cells"])
    out["verdict"] = {"independence_rejected_all": a_ok, "off": {"fixed_norm": off_f, "independent": off_i},
                      "R12_pass": a_ok and off_f <= 2 and off_f < off_i}
    print(f"{label} verdict:", out["verdict"], flush=True)
    (HERE / outfile).write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--choose", action="store_true")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.choose:
        choose()
    if a.test:
        test()
