"""Are repeated Babai attempts on one LWE instance independent? A test of the lattice estimator's
repetition model against a fixed-error model.

Toy parameters only (q = 3329, m = n). Nothing here is a security claim about ML-KEM.

Background. The lattice estimator's PrimalHybrid charges amplify(0.99, p) = log(0.01) / log(1 - p) repetitions,
i.e. it treats attempts as independent with one success probability p, whose Babai part is Wunderer's sphere
formula at the fixed radius sqrt(d) * sigma. On a single instance the error is fixed, so every attempt sees the
same ||o||. de Perthuis-Trenkic (PQCrypto 2026, ePrint 2025/2195) make the analogous point for the uSVP route.

Re-randomisation. Attempt j permutes the samples (Q_j) and the secret coordinates (P_j): A_j = A[Q_j][:, P_j],
b_j = b[Q_j], s_j = s[P_j], e_j = e[Q_j]. This is an isometric copy of the same instance, its offset
o_j = (-s_j, e_j) has the same norm as o, and its basis is reduced from scratch (LLL, or LLL then BKZ-beta with
the same settings as toy_lwe_test.py). Babai on basis j succeeds exactly when |<o_j, u_i>| < ||b*_i|| / 2 at every
level, so success is computed from the projections; the identity is checked against the GPU decoder on a sample.

Models of P(target t solved within the first k attempts), both using each basis's own measured profile:
  independent  1 - prod_{j<k} (1 - p_j(d sigma^2))        the estimator's model: one radius for every instance
  fixed error  1 - prod_{j<k} (1 - p_j(||o_t||^2))        the same formula at the instance's own error norm
  p_j(r) = prod_i I_x(1/2, (d-1)/2), x = ||b*_i||^2 / (4 r)   (the estimator's prob.babai with norm sqrt(r))

Settings: LLL n = 80 with K = 256 attempts, and BKZ-20 n = 100 with K = 64 attempts; 16 lattices x 200 targets;
eta in {2, 3}; the same bases serve both eta.

Rules, set before any run:
  R4 independence. Statistic: variance across targets of the number of successes in K attempts. Null: success
     depends on the basis but not on the target (shuffle each basis's success column across the targets of its
     lattice; 10,000 shuffles). Independence is rejected at a (setting, eta) if the permutation p-value < 0.01.
  R5 model. For k in {K/8, K/2, K} the predicted share of targets solved within k attempts is "off" if it falls
     outside the 99% Wilson interval of the measured share. Also for the share never solved in K attempts.
     The fixed-error model wins if it is off in fewer of these 16 cells (2 settings x 2 eta x 4) than the
     independent model, and in at most 4 of them.
  Outside the rules: Spearman correlation of success count with ||o||; how much of the excess variance the
     fixed-error model explains (if not all of it, bases of one lattice are correlated beyond ||o||).

Run:
  WSL (fpylll):  python retry_study.py --reduce      bases into $TOY_LWE_CACHE/retry
  Windows (GPU): uv run ... python retry_study.py --analyse
"""
import argparse
import json
import math
import os
import pathlib
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import toy_lwe_test as T  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
TAG = T.TAGS["heldout"]
SETTINGS = [(2, 80, 256), (20, 100, 64)]  # (beta, n, attempts K)
LATTICES, TARGETS, ETAS = 16, 200, (2, 3)
RETRY = T.CACHE / "retry"


def perms(n, idx, j):
    rng = np.random.default_rng([TAG, n, idx, j, 7])
    return rng.permutation(n), rng.permutation(n)  # P (secret coordinates), Q (samples)


def base_path(beta, n, idx, j):
    return RETRY / f"b{beta}_n{n}_i{idx}_j{j}.npy"


def reduce_one(job):
    beta, n, idx, j = job
    path = base_path(beta, n, idx, j)
    if not path.exists():
        P, Qp = perms(n, idx, j)
        B, _ = T.reduce_basis(T.make_A(TAG, n, n, idx)[Qp][:, P], beta, 900)
        tmp = path.with_name(path.stem + f".{os.getpid()}.tmp.npy")
        np.save(tmp, B)
        tmp.replace(path)
    return job


def reduce_all(workers):
    RETRY.mkdir(parents=True, exist_ok=True)
    jobs = [(b, n, i, j) for b, n, K in SETTINGS for i in range(LATTICES) for j in range(K)]
    start = time.perf_counter()
    with ProcessPoolExecutor(workers) as pool:
        for k, f in enumerate(as_completed([pool.submit(reduce_one, jb) for jb in jobs]), 1):
            b, n, i, j = f.result()
            if k % 64 == 0 or k == len(jobs):
                print(f"  [{k}/{len(jobs)}] {time.perf_counter() - start:6.0f}s  last: {T.beta_name(b)} n={n} lattice {i} basis {j}",
                      flush=True)


def instance_offsets(n, idx, eta):
    tg = T.make_targets(T.make_A(TAG, n, n, idx), TAG, eta, idx, TARGETS)
    s = np.stack([x[0] for x in tg])
    e = np.stack([x[1] for x in tg])
    return s, e, np.stack([x[2] for x in tg])


def p_sphere(nrm, r):
    """Estimator's prob.babai on profile nrm (squared GS norms) for radius^2 r (array)."""
    from scipy.special import betainc
    d = len(nrm)
    x = np.minimum(1.0, nrm[None, :] / (4.0 * np.asarray(r, float)[:, None]))
    return np.exp(np.log(np.maximum(betainc(0.5, (d - 1) / 2, x), 1e-300)).sum(1))


def analyse():
    import torch
    import toy_lwe_gpu as G
    from scipy.stats import spearmanr

    def wilson(k, n, z=2.5758293035489):
        p = k / n
        c = (p + z * z / (2 * n)) / (1 + z * z / n)
        h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
        return (0.0 if k == 0 else c - h), (1.0 if k == n else c + h)

    out = {}
    for beta, n, K in SETTINGS:
        d = 2 * n
        S = {eta: np.zeros((LATTICES, TARGETS, K), bool) for eta in ETAS}
        Pind = {eta: np.zeros((LATTICES, TARGETS, K)) for eta in ETAS}
        Pfix = {eta: np.zeros((LATTICES, TARGETS, K)) for eta in ETAS}
        norms = {eta: np.zeros((LATTICES, TARGETS)) for eta in ETAS}
        checked = 0
        for idx in range(LATTICES):
            offs = {eta: instance_offsets(n, idx, eta) for eta in ETAS}
            for j in range(K):
                B = np.load(base_path(beta, n, idx, j))
                Bs, nrm = T.gso(B)
                U = torch.as_tensor(Bs / np.sqrt(nrm)[:, None], dtype=G.F64, device=G.DEV)
                half = torch.as_tensor(np.sqrt(nrm) / 2, dtype=G.F64, device=G.DEV)
                P, Qp = perms(n, idx, j)
                for eta in ETAS:
                    s, e, b = offs[eta]
                    o = np.concatenate([-s[:, P], e[:, Qp]], 1)
                    ot = torch.as_tensor(o, dtype=G.F64, device=G.DEV)
                    S[eta][idx, :, j] = ((ot @ U.T).abs() < half).all(1).cpu().numpy()
                    r = (o * o).sum(1)
                    norms[eta][idx] = r
                    Pind[eta][idx, :, j] = p_sphere(nrm, [d * eta / 2])[0]
                    Pfix[eta][idx, :, j] = p_sphere(nrm, r)
                    if idx == 0 and j < 4:  # the identity, against the real decoder
                        ts = np.concatenate([np.zeros((TARGETS, n), np.int64), b[:, Qp]], 1)
                        dec = G.decode_all(("babai",), B, Bs, nrm, ts, math.sqrt(eta / 2))
                        got = np.array([np.array_equal(np.rint(p[:n]).astype(np.int64), s[t, P]) for t, (p, *_) in enumerate(dec)])
                        assert np.array_equal(got, S[eta][idx, :, j]), "Babai identity fails on a permuted basis"
                        checked += TARGETS
            print(f"  {T.beta_name(beta)} n={n} lattice {idx}: " +
                  "  ".join(f"eta={eta} mean success {S[eta][idx].mean():.4f}" for eta in ETAS), flush=True)

        for eta in ETAS:
            Sx, key = S[eta], f"{beta},{n},{eta}"
            counts = Sx.sum(2)  # (lattice, target)
            stat = counts.var()
            g = torch.Generator(device=G.DEV).manual_seed(beta * 1000 + n * 10 + eta)
            St = torch.as_tensor(Sx, dtype=torch.float32, device=G.DEV)
            more, reps = 0, 10_000
            for _ in range(reps // 100):  # 100 shuffles per batch; column-wise shuffle within lattice
                keys = torch.rand((100, LATTICES, TARGETS, K), generator=g, device=G.DEV)
                idxs = keys.argsort(2)
                sh = torch.gather(St.expand(100, -1, -1, -1), 2, idxs).sum(3)
                more += int((sh.flatten(1).var(1, unbiased=False) >= stat).sum())
            p_perm = (more + 1) / (reps + 1)

            cells = []
            for k in (K // 8, K // 2, K, "never"):
                if k == "never":
                    meas = int((counts == 0).sum())
                    pi = float(np.prod(1 - Pind[eta], 2).mean())
                    pf = float(np.prod(1 - Pfix[eta], 2).mean())
                else:
                    meas = int(Sx[:, :, :k].any(2).sum())
                    pi = float((1 - np.prod(1 - Pind[eta][:, :, :k], 2)).mean())
                    pf = float((1 - np.prod(1 - Pfix[eta][:, :, :k], 2)).mean())
                N = LATTICES * TARGETS
                lo, hi = wilson(meas, N)
                cells.append({"k": k, "measured": meas / N, "ci": [lo, hi], "independent": pi, "fixed": pf,
                              "independent_off": not lo <= pi <= hi, "fixed_off": not lo <= pf <= hi})
            # Excess variance: measured vs each model's predicted variance of the counts.
            def model_var(Pm):
                mean_t = Pm.sum(2)
                return float((Pm * (1 - Pm)).sum(2).mean() + mean_t.var())
            rho = spearmanr(norms[eta].ravel(), counts.ravel()).correlation
            out[key] = {"beta": beta, "n": n, "eta": eta, "K": K, "mean_success": float(Sx.mean()), "count_var": float(stat),
                        "var_independent": model_var(Pind[eta]), "var_fixed": model_var(Pfix[eta]), "perm_p": p_perm,
                        "independence_rejected": p_perm < 0.01, "cells": cells, "spearman_norm_count": float(rho),
                        "counts": counts.astype(int).tolist(), "norms": norms[eta].astype(int).tolist()}
            c = out[key]
            print(f"{T.beta_name(beta)} n={n} eta={eta} K={K}: success/attempt {c['mean_success']:.4f}; count variance {stat:.2f} "
                  f"(independent {c['var_independent']:.2f}, fixed-error {c['var_fixed']:.2f}); perm p={p_perm:.4g}; "
                  f"Spearman(||o||, count) {rho:+.3f}", flush=True)
            for cell in cells:
                print(f"    k={cell['k']!s:>5}: measured {100 * cell['measured']:5.1f}% ({100 * cell['ci'][0]:.1f}-{100 * cell['ci'][1]:.1f})  "
                      f"independent {100 * cell['independent']:5.1f}%{' OFF' if cell['independent_off'] else ''}  "
                      f"fixed-error {100 * cell['fixed']:5.1f}%{' OFF' if cell['fixed_off'] else ''}", flush=True)
        print(f"  identity checked on {checked} decodes", flush=True)

    offs = {m: sum(c[f"{m}_off"] for v in out.values() for c in v["cells"]) for m in ("independent", "fixed")}
    out["verdict"] = {"R4_rejected": [k for k, v in out.items() if v["independence_rejected"]], "off": offs,
                      "R5_fixed_wins": offs["fixed"] < offs["independent"] and offs["fixed"] <= 4}
    (HERE / "retry_study_results.json").write_text(json.dumps(out))
    print("verdict:", out["verdict"], flush=True)


def exact_curve(nrm, radii2, M, seed):
    """P(Babai succeeds | ||o||^2 = r) for o of fixed norm and uniformly random direction, exactly (no product over
    levels): with z uniform on the unit sphere, success iff sqrt(r) < rho(z) = min_i (||b*_i|| / 2) / |z_i|.
    One GPU Monte Carlo per basis gives the whole curve in r."""
    import torch
    import toy_lwe_gpu as G
    g = torch.Generator(device=G.DEV).manual_seed(seed)
    d = len(nrm)
    half = torch.as_tensor(np.sqrt(nrm) / 2, dtype=G.F64, device=G.DEV)
    rho = []
    for _ in range(0, M, 25_000):
        z = torch.randn((25_000, d), generator=g, device=G.DEV, dtype=G.F64)
        z = z / z.norm(dim=1, keepdim=True)
        rho.append((half / z.abs()).min(1).values)
    rho = torch.sort(torch.cat(rho)).values
    r = torch.as_tensor(np.sqrt(np.asarray(radii2, float)), dtype=G.F64, device=G.DEV)
    return (1.0 - torch.searchsorted(rho, r).to(G.F64) / len(rho)).cpu().numpy()


def block_probs(Bs, nrm, n, s2, e2, M, seed):
    """Two-block exact law. Re-randomisation permutes coordinates only within the secret block (first n) and within
    the sample block, so for o = (-s, e) the invariant is the pair (||s||^2, ||e||^2), not just ||o||^2. Success
    probability for each target t: P(|<(a_t z1, b_t z2), u_i>| < ||b*_i|| / 2 for all i), z1, z2 uniform on the unit
    spheres of the two blocks, a_t = ||s_t||, b_t = ||e_t||. No free parameters."""
    import torch
    import toy_lwe_gpu as G
    g = torch.Generator(device=G.DEV).manual_seed(seed)
    U = torch.as_tensor(Bs / np.sqrt(nrm)[:, None], dtype=G.F64, device=G.DEV)
    half = torch.as_tensor(np.sqrt(nrm) / 2, dtype=G.F64, device=G.DEV)
    a = torch.as_tensor(np.sqrt(s2), dtype=G.F64, device=G.DEV)
    b = torch.as_tensor(np.sqrt(e2), dtype=G.F64, device=G.DEV)
    hits = torch.zeros(len(s2), dtype=G.F64, device=G.DEV)
    d = U.shape[1]
    for _ in range(0, M, 4000):
        z1 = torch.randn((4000, n), generator=g, device=G.DEV, dtype=G.F64)
        z2 = torch.randn((4000, d - n), generator=g, device=G.DEV, dtype=G.F64)
        X1 = (z1 / z1.norm(dim=1, keepdim=True)) @ U[:, :n].T  # (M, d)
        X2 = (z2 / z2.norm(dim=1, keepdim=True)) @ U[:, n:].T
        for t0 in range(0, len(s2), 50):
            P = a[t0:t0 + 50, None, None] * X1[None] + b[t0:t0 + 50, None, None] * X2[None]  # (50, M, d)
            hits[t0:t0 + 50] += (P.abs() < half).all(2).sum(1)
    return (hits / (M // 4000 * 4000)).cpu().numpy()


def multiset_probs(Bs, nrm, n, o, M, seed):
    """Block-multiset law. The re-randomisation group (permutations within the secret block and within the sample
    block) leaves exactly the two coordinate multisets of o invariant. For each target: the share of M random
    within-block permutations of its own offset that pass every Babai level of this basis. No free parameters."""
    import torch
    import toy_lwe_gpu as G
    g = torch.Generator(device=G.DEV).manual_seed(seed)
    U = torch.as_tensor(Bs / np.sqrt(nrm)[:, None], dtype=G.F64, device=G.DEV)
    half = torch.as_tensor(np.sqrt(nrm) / 2, dtype=G.F64, device=G.DEV)
    O = torch.as_tensor(o, dtype=G.F64, device=G.DEV)
    d = O.shape[1]
    idx = torch.cat([torch.rand((M, n), generator=g, device=G.DEV).argsort(1),
                     n + torch.rand((M, d - n), generator=g, device=G.DEV).argsort(1)], 1)  # (M, d)
    out = torch.empty(len(o), dtype=G.F64, device=G.DEV)
    for t in range(len(o)):
        out[t] = ((O[t][idx] @ U.T).abs() < half).all(1).to(G.F64).mean()
    return out.cpu().numpy()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reduce", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--workers", type=int, default=18)
    a = ap.parse_args()
    if a.reduce:
        reduce_all(a.workers)
    if a.analyse:
        analyse()
