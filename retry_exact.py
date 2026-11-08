"""Exact fixed-norm model for repeated Babai attempts (see retry_study.py for the setup).

Model "exact fixed norm": attempt j on target t succeeds with F_j(||o_t||^2), the probability that a vector of that
norm in a uniformly random direction passes every level of basis j jointly (retry_study.exact_curve), and attempts
are independent given ||o_t||. No free parameters. Compared with the independent model (one radius sqrt(d)sigma,
product over levels) and the product-over-levels fixed-norm model of retry_study.py.

--explore   on the bases of retry_study.py (already seen when this model was proposed: exploratory only)
--heldout   on fresh settings, judged by rule R6 below (fixed before those bases were reduced)

R6. Settings LLL n = 76 (K = 256) and BKZ-10 n = 90 (K = 64), eta in {2, 3}, 16 lattices x 200 targets, fresh
    instances (tag 5). Cells: share solved within K/8, K/2, K attempts and never solved, 99% Wilson intervals
    (16 cells). The exact fixed-norm model passes if it is off in at most 2 cells and in fewer cells than the
    independent model; and if its predicted variance of success counts is within 25% of the measured one in all
    4 (setting, eta). Monte Carlo: 200,000 directions per basis.

R6 failed (8 cells off, all 8 at LLL; LLL variance off). On BKZ bases the exact model was inside in all 16 cells
seen so far (BKZ-20 n=100 exploratory, BKZ-10 n=90 held out), a split made after R6. R7 tests that claim on new data.

R7 (fixed 7 Nov 2026, before any of these bases were reduced). Claim: for BKZ-reduced bases, repeated Babai
    attempts on one instance are independent given ||o|| and follow the exact fixed-norm law. Settings BKZ-15 n = 90
    and BKZ-20 n = 110, K = 64, eta in {2, 3}, 16 lattices x 200 targets, fresh instances (tag 6), same
    re-randomisation and reduction as before. Same 16 cells and 99% Wilson intervals as R6. The claim holds if the
    exact model is off in at most 2 cells and in fewer cells than the independent model, and its predicted variance of
    success counts is within 25% of the measured one in all 4 (setting, eta). Nothing else is reported as a test.

R7 result: exact model off in 0 of 16 cells (independent: 5), but the variance criterion FAILED. BKZ-20 n = 110 was
    degenerate (0.01% success per attempt at eta = 2, no success at all at eta = 3), so the variance ratio there is
    meaningless or undefined; the rule had no guard for that. At BKZ-15 n = 90 the variance was within 3%.

R8 (fixed 8 Nov 2026, before any of these bases were reduced). Same claim and test as R7, on settings chosen from the
    earlier calibration to give roughly 1-30% success per attempt: BKZ-20 n = 95 and BKZ-10 n = 85, K = 64,
    eta in {2, 3}, 16 lattices x 200 targets, fresh instances (tag 7). Pass: exact model off in at most 2 of the
    16 cells and in fewer than the independent model, and predicted count variance within 25% of measured in every
    (setting, eta) with at least 50 successes in total; a (setting, eta) with fewer than 50 successes is reported
    as degenerate and excluded from the variance criterion (but not from the cells). If more than one of the four is
    degenerate, R8 counts as failed.

R8 result: PASSED (exact model 0 of 16 cells off, independent 12; variance within 2.7-6.3%; none degenerate).

R9 (fixed 8 Nov 2026, before these bases were reduced). Claim: for LLL-reduced bases, the dependence between repeated
    attempts is explained by the instance alone through the block-multiset law (retry_study.multiset_probs: success
    probability of a random within-block permutation of the instance's own offset on each basis; no free parameters).
    Exploratory basis for the claim: LLL n = 80, eta = 2, 4 lattices (count variance 22.1 predicted vs 24.4 measured).
    Setting LLL n = 78, K = 128, eta in {2, 3}, 16 lattices x 200 targets, fresh instances (tag 8), 2,000
    permutations per (basis, target). Cells: share solved within 16, 64, 128 attempts and never solved, 99% Wilson
    (8 cells). Pass: block-multiset model off in at most 1 cell and in fewer than the independent model, and its
    predicted count variance within 25% of measured at both eta (degeneracy guard as in R8).
"""
import argparse
import json
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import retry_study as R  # noqa: E402
import toy_lwe_test as T  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
HELDOUT = [(2, 76, 256), (10, 90, 64)]
CONFIRM = [(15, 90, 64), (20, 110, 64)]
CONFIRM2 = [(20, 95, 64), (10, 85, 64)]
LLLCONFIRM = [(2, 78, 128)]
TAGSETS = {5: HELDOUT, 6: CONFIRM, 7: CONFIRM2, 8: LLLCONFIRM, 11: LLLCONFIRM}
MULTISET_TAGS = (8, 11)  # tag 11: R11, scrambled LLL bases (retry_lll.py)
M_DIRS = 200_000


def wilson(k, n, z=2.5758293035489):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (0.0 if k == 0 else c - h), (1.0 if k == n else c + h)


def run(settings, tag, label):
    import torch
    import toy_lwe_gpu as G
    R.TAG = tag
    out = {}
    for beta, n, K in settings:
        d = 2 * n
        S, P = {}, {}
        for eta in R.ETAS:
            S[eta] = np.zeros((R.LATTICES, R.TARGETS, K), bool)
            P[eta] = {m: np.zeros((R.LATTICES, R.TARGETS, K)) for m in ("independent", "product", "exact")}
            if tag in MULTISET_TAGS:
                P[eta]["multiset"] = np.zeros((R.LATTICES, R.TARGETS, K))
        for idx in range(R.LATTICES):
            offs = {eta: R.instance_offsets(n, idx, eta) for eta in R.ETAS}
            for j in range(K):
                B = np.load(R.base_path(beta, n, idx, j) if tag == T.TAGS["heldout"] else heldout_path(beta, n, idx, j, tag))
                Bs, nrm = T.gso(B)
                U = torch.as_tensor(Bs / np.sqrt(nrm)[:, None], dtype=G.F64, device=G.DEV)
                half = torch.as_tensor(np.sqrt(nrm) / 2, dtype=G.F64, device=G.DEV)
                Pp, Qp = R.perms(n, idx, j)
                radii = {eta: (np.concatenate([offs[eta][0][:, Pp], offs[eta][1][:, Qp]], 1) ** 2).sum(1) for eta in R.ETAS}
                allr = np.concatenate([radii[eta] for eta in R.ETAS] + [np.array([d * eta / 2 for eta in R.ETAS])])
                F = exact = R.exact_curve(nrm, allr, M_DIRS, seed=(tag * 1000 + idx) * 1000 + j)
                at = 0
                for eta in R.ETAS:
                    s, e, _ = offs[eta]
                    o = np.concatenate([-s[:, Pp], e[:, Qp]], 1)
                    S[eta][idx, :, j] = ((torch.as_tensor(o, dtype=G.F64, device=G.DEV) @ U.T).abs() < half).all(1).cpu().numpy()
                    P[eta]["exact"][idx, :, j] = F[at:at + R.TARGETS]
                    P[eta]["product"][idx, :, j] = R.p_sphere(nrm, radii[eta])
                    P[eta]["independent"][idx, :, j] = R.p_sphere(nrm, [d * eta / 2])[0]
                    if tag in MULTISET_TAGS:
                        P[eta]["multiset"][idx, :, j] = R.multiset_probs(Bs, nrm, n, o, 2000, seed=(idx * 1000 + j) * 10 + eta)
                    at += R.TARGETS
            print(f"  {label} {T.beta_name(beta)} n={n} lattice {idx} done", flush=True)
        for eta in R.ETAS:
            key, counts, N = f"{beta},{n},{eta}", S[eta].sum(2), R.LATTICES * R.TARGETS
            row = {"K": K, "mean_success": float(S[eta].mean()), "count_var": float(counts.var()), "models": {}}
            for m, Pm in P[eta].items():
                cells = []
                for k in (K // 8, K // 2, K, "never"):
                    if k == "never":
                        meas, pred = int((counts == 0).sum()), float(np.prod(1 - Pm, 2).mean())
                    else:
                        meas, pred = int(S[eta][:, :, :k].any(2).sum()), float((1 - np.prod(1 - Pm[:, :, :k], 2)).mean())
                    lo, hi = wilson(meas, N)
                    cells.append({"k": k, "measured": meas / N, "ci": [lo, hi], "pred": pred, "off": not lo <= pred <= hi})
                var = float((Pm * (1 - Pm)).sum(2).mean() + Pm.sum(2).var())
                row["models"][m] = {"cells": cells, "var": var, "mean": float(Pm.mean())}
            out[key] = row
            print(f"{label} {T.beta_name(beta)} n={n} eta={eta} K={K}: success/attempt measured {row['mean_success']:.4f}, "
                  f"count variance measured {row['count_var']:.3f}", flush=True)
            for m, v in row["models"].items():
                print(f"    {m:<12} mean {v['mean']:.4f}  var {v['var']:.3f}  " + "  ".join(
                    f"k={c['k']}: {100 * c['pred']:.1f}% vs {100 * c['measured']:.1f}%{' OFF' if c['off'] else ''}" for c in v["cells"]),
                    flush=True)
    if tag in MULTISET_TAGS:  # R9 (tag 8), R11 (tag 11, scrambled LLL): same criteria
        succ = {k: r["mean_success"] * r["K"] * R.LATTICES * R.TARGETS for k, r in out.items()}
        degenerate = [k for k, v in succ.items() if v < 50]
        var_ok = all(abs(r["models"]["multiset"]["var"] / r["count_var"] - 1) <= 0.25 for k, r in out.items() if k not in degenerate)
        offs9 = {m: sum(c["off"] for r in out.values() for c in r["models"][m]["cells"]) for m in ("independent", "exact", "multiset")}
        out["verdict"] = {"off": offs9, "degenerate": degenerate, "successes": succ, "multiset_var_within_25pct": var_ok,
                          f"{label}_pass": offs9["multiset"] <= 1 and offs9["multiset"] < offs9["independent"] and var_ok and not degenerate}
        print(label, "verdict:", out["verdict"], flush=True)
        return out
    if tag == 7:  # R8: degeneracy guard, fixed before the run
        succ = {k: r["mean_success"] * r["K"] * R.LATTICES * R.TARGETS for k, r in out.items()}
        degenerate = [k for k, v in succ.items() if v < 50]
        var_ok8 = all(abs(r["models"]["exact"]["var"] / r["count_var"] - 1) <= 0.25 for k, r in out.items() if k not in degenerate)
        offs8 = {m: sum(c["off"] for r in out.values() for c in r["models"][m]["cells"]) for m in ("independent", "exact")}
        out["verdict"] = {"off": offs8, "degenerate": degenerate, "successes": succ, "exact_var_within_25pct_nondegenerate": var_ok8,
                          "R8_pass": offs8["exact"] <= 2 and offs8["exact"] < offs8["independent"] and var_ok8 and len(degenerate) <= 1}
        print(label, "verdict:", out["verdict"], flush=True)
        return out
    offs = {m: sum(c["off"] for r in out.values() for c in r["models"][m]["cells"]) for m in ("independent", "product", "exact")}
    var_ok = all(abs(r["models"]["exact"]["var"] / r["count_var"] - 1) <= 0.25 for r in out.values())
    out["verdict"] = {"off": offs, "exact_var_within_25pct": var_ok,
                      "R6_pass": offs["exact"] <= 2 and offs["exact"] < offs["independent"] and var_ok}
    print(label, "verdict:", out["verdict"], flush=True)
    return out


def heldout_path(beta, n, idx, j, tag=5):
    if tag == 11:  # scrambled LLL bases (retry_lll.py)
        return R.RETRY / f"u{tag}_n{n}_i{idx}_j{j}.npy"
    return R.RETRY / f"t{tag}_b{beta}_n{n}_i{idx}_j{j}.npy"


def reduce_heldout(workers, tag=5):
    """WSL: fresh instances (tag 5 for R6, tag 6 for R7), same permutation re-randomisation and reduction."""
    import time
    from concurrent.futures import ProcessPoolExecutor, as_completed
    R.RETRY.mkdir(parents=True, exist_ok=True)
    jobs = [(b, n, i, j, tag) for b, n, K in TAGSETS[tag] for i in range(R.LATTICES) for j in range(K)]
    start = time.perf_counter()
    with ProcessPoolExecutor(workers) as pool:
        futs = [pool.submit(_reduce5, jb) for jb in jobs]
        for k, f in enumerate(as_completed(futs), 1):
            f.result()
            if k % 128 == 0 or k == len(jobs):
                print(f"  [{k}/{len(jobs)}] {time.perf_counter() - start:6.0f}s", flush=True)


def _reduce5(job):
    import os
    beta, n, idx, j, tag = job
    path = heldout_path(beta, n, idx, j, tag)
    if not path.exists():
        R.TAG = tag
        Pp, Qp = R.perms(n, idx, j)
        B, _ = T.reduce_basis(T.make_A(tag, n, n, idx)[Qp][:, Pp], beta, 900)
        tmp = path.with_name(path.stem + f".{os.getpid()}.tmp.npy")
        np.save(tmp, B)
        tmp.replace(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--explore", action="store_true")
    ap.add_argument("--reduce-heldout", action="store_true")
    ap.add_argument("--heldout", action="store_true")
    ap.add_argument("--reduce-confirm", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--reduce-confirm2", action="store_true")
    ap.add_argument("--confirm2", action="store_true")
    ap.add_argument("--reduce-lll", action="store_true")
    ap.add_argument("--confirm-lll", action="store_true")
    ap.add_argument("--r11", action="store_true", help="rule R11 on the scrambled LLL bases of retry_lll.py")
    a = ap.parse_args()
    if a.r11:
        res = run(LLLCONFIRM, 11, "R11")
        (HERE / "retry_r11.json").write_text(json.dumps(res))
    if a.reduce_lll:
        reduce_heldout(18, tag=8)
    if a.confirm_lll:
        res = run(LLLCONFIRM, 8, "R9")
        (HERE / "retry_exact_lll.json").write_text(json.dumps(res))
    if a.reduce_confirm2:
        reduce_heldout(18, tag=7)
    if a.confirm2:
        res = run(CONFIRM2, 7, "R8")
        (HERE / "retry_exact_confirm2.json").write_text(json.dumps(res))
    if a.reduce_confirm:
        reduce_heldout(18, tag=6)
    if a.confirm:
        res = run(CONFIRM, 6, "R7")
        (HERE / "retry_exact_confirm.json").write_text(json.dumps(res))
    if a.explore:
        res = run(R.SETTINGS, T.TAGS["heldout"], "explore")
        (HERE / "retry_exact_explore.json").write_text(json.dumps(res))
    if a.reduce_heldout:
        reduce_heldout(18)
    if a.heldout:
        res = run(HELDOUT, 5, "R6")
        (HERE / "retry_exact_heldout.json").write_text(json.dumps(res))
