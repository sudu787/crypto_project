"""Item 7: repeated Babai attempts on the public TU Darmstadt LWE challenge instances (lwe_challenge/LWE_<n>_<a>.txt,
downloaded 8 Nov 2026 from latticechallenge.org with the user's approval).

File format: n, m (= 1600), q, alpha, then b (m values), then A (m rows of n values); b = A s + e mod q, s uniform mod q,
e Gaussian with sigma = alpha * q. The secret is not published.

Instances. A file's samples are split into disjoint blocks of mm samples; block t is one LWE instance (A_t, b_t) with
its own error e_t (all blocks share s, which does not enter the offset). Lattice: L_t = {y in Z^mm : y = A_t x mod q},
basis [[I_n, (A2 A1^-1)^T], [0, q I]] for the permuted block (A1 = first n permuted rows, invertible mod q);
the offset of b_t from L_t is e_t (mm coordinates). Attempt j permutes the block's samples (fresh permutation),
builds that basis and reduces it with BKZ-beta (fplll BKZ 2.0, long double), as in the toy study.

Solving without the secret: Babai on (basis, b_t) gives v; s_hat = A1^-1 v_1 mod q; an attempt succeeds iff the
residual b - A s_hat over all 1600 samples is Gaussian-sized (norm < 2 sqrt(1600) sigma; a wrong s_hat gives a
residual of norm ~ q sqrt(1600/12)). Once s is known, e_t is known for every block and success on every basis is
given by the projection identity |<e_t, u_i>| < ||b*_i||/2; that identity is checked against real Babai on the
first 64 bases decoded after s is found (and on all bases decoded before).

Probe (one basis per candidate, exact-law success at the expected norm mm sigma^2, no outcomes; lwe_challenge_probe
log): only n=40 alpha=0.005 (mm=120: BKZ-20 18.6%, BKZ-30 33.4%) and n=45 alpha=0.005 (mm=135: BKZ-30 4.35%,
BKZ-20 0.48%) are away from zero; every alpha >= 0.010 file and n >= 50 is ~0 for BKZ <= 30 with mm <= 3n.

R13 (fixed 8 Nov 2026, before any R13 basis was reduced). Settings: n=40 alpha=0.005 mm=120 BKZ-20 (13 instances) and
    n=45 alpha=0.005 mm=135 BKZ-30 (11 instances); K = 64 attempts per instance. For each instance t and model M,
    z_t = (count_t - sum_j p_tj) / sqrt(sum_j p_tj (1 - p_tj)) with p_tj the model's success probability on basis j:
    exact fixed-norm law at the instance's own ||e_t||^2 (M = exact), or the estimator's prob.babai at radius
    sqrt(mm) sigma (M = independent). Pearson X^2 = sum_t z_t^2 over the 24 instances, compared with chi^2_24.
    Pass: p(X^2_exact) > 0.01 and p(X^2_independent) < 0.01. Also reported (not part of the rule): the R4 permutation
    test within each setting. Reported either way.
"""
import argparse
import json
import math
import os
import pathlib
import sys
import time

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import toy_lwe_test as T  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
DIR = HERE / "lwe_challenge"
CACHE = T.CACHE / "challenge"
SETTINGS = [(40, "005", 120, 20), (45, "005", 135, 30)]
K13 = 64


def load(n, a):
    lines = (DIR / f"LWE_{n}_{a}.txt").read_text().split("\n")
    n_, m, q, alpha = int(lines[0]), int(lines[1]), int(lines[2]), float(lines[3])
    b = np.array(lines[4].strip("[] ").split(), dtype=np.int64)
    A = np.array([ln.strip("[] ").split() for ln in lines[5:5 + m]], dtype=np.int64)
    assert A.shape == (m, n_) and len(b) == m
    return {"n": n_, "m": m, "q": q, "alpha": alpha, "sigma": alpha * q, "A": A, "b": b}


def inv_mod(M, q):
    """Inverse of a square integer matrix mod prime q (Gauss-Jordan); None if singular."""
    n = len(M)
    Aug = np.concatenate([M % q, np.eye(n, dtype=np.int64)], 1)
    for c in range(n):
        piv = next((r for r in range(c, n) if Aug[r, c] % q), None)
        if piv is None:
            return None
        Aug[[c, piv]] = Aug[[piv, c]]
        Aug[c] = Aug[c] * pow(int(Aug[c, c]), -1, q) % q
        for r in range(n):
            if r != c and Aug[r, c]:
                Aug[r] = (Aug[r] - Aug[r, c] * Aug[c]) % q
    return Aug[:, n:]


def perm_for(n, a, mm, t, j):
    return np.random.default_rng([13, n, int(a), mm, t, j]).permutation(mm)


def block(inst, mm, t):
    sl = slice(t * mm, (t + 1) * mm)
    return inst["A"][sl], inst["b"][sl]


def basis(At, q):
    """Basis of {y : y = At x mod q} (rows), with A1 = first n rows of At invertible mod q."""
    mm, n = At.shape
    A1inv = inv_mod(At[:n], q)
    if A1inv is None:
        return None, None
    C = At[n:] @ A1inv % q  # y2 = C y1
    B = np.zeros((mm, mm), dtype=np.int64)
    B[:n, :n] = np.eye(n, dtype=np.int64)
    B[:n, n:] = C.T
    B[n:, n:] = q * np.eye(mm - n, dtype=np.int64)
    return B, A1inv


def reduce(B, beta):
    from fpylll import BKZ, LLL, IntegerMatrix
    M = IntegerMatrix.from_matrix(B.tolist())
    LLL.reduction(M)
    if beta > 2:
        strat = os.environ.get("FPLLL_STRATEGY", "/home/sudu/micromamba/envs/sage/share/fplll/strategies/default.json")
        BKZ.reduction(M, BKZ.Param(block_size=beta, strategies=strat, flags=BKZ.AUTO_ABORT | BKZ.MAX_LOOPS | BKZ.MAX_TIME,
                                   max_loops=16, max_time=1800), float_type="ld")
    d = len(B)
    return np.array([[M[i, k] for k in range(d)] for i in range(d)], dtype=np.int64)


def path(n, a, mm, beta, t, j):
    return CACHE / f"c{n}_{a}_m{mm}_b{beta}_t{t}_j{j}.npy"


def make(job):
    n, a, mm, beta, t, j = job
    p = path(*job)
    if p.exists():
        return job
    inst = load(n, a)
    At, _ = block(inst, mm, t)
    jj = j
    while True:  # a permutation whose first n rows are invertible mod q (almost always the first)
        P = perm_for(n, a, mm, t, jj)
        B, _ = basis(At[P], inst["q"])
        if B is not None:
            break
        jj += 10_000
    R = reduce(B, beta)
    tmp = p.with_name(p.stem + f".{os.getpid()}.tmp.npy")
    np.save(tmp, R)
    tmp.replace(p)
    (p.with_suffix(".json")).write_text(json.dumps({"perm_seed_j": jj}))
    return job


def run_pool(jobs, workers):
    from concurrent.futures import ProcessPoolExecutor, as_completed
    CACHE.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    with ProcessPoolExecutor(workers) as pool:
        for k, f in enumerate(as_completed([pool.submit(make, jb) for jb in jobs]), 1):
            f.result()
            if k % 32 == 0 or k == len(jobs):
                print(f"  [{k}/{len(jobs)}] {time.perf_counter() - t0:6.0f}s", flush=True)


def exact_F(nrm, r, M=200_000, seed=0):
    rng = np.random.default_rng(seed)
    c = np.sqrt(nrm) / 2
    rho = []
    for _ in range(M // 20_000):
        z = rng.standard_normal((20_000, len(nrm)))
        z /= np.linalg.norm(z, axis=1, keepdims=True)
        rho.append((c / np.abs(z)).min(1))
    rho = np.sort(np.concatenate(rho))
    return 1 - np.searchsorted(rho, np.sqrt(np.asarray(r, float))) / len(rho)


def prod_babai(nrm, r):
    """The estimator's prob.babai (per-level product) at radius sqrt(r)."""
    from scipy.special import betainc
    d = len(nrm)
    x = np.minimum(1.0, nrm / (4.0 * r))
    return float(np.exp(np.log(np.maximum(betainc(0.5, (d - 1) / 2, x), 1e-300)).sum()))


FILES = [(n, a) for n in (40, 45, 50, 55) for a in ("005", "010", "015")]
PROBE = [(n, a, mm, beta) for n, a in FILES for mm in (2 * n, 3 * n) for beta in (20, 30)]


def probe_predict():
    rows = []
    for n, a, mm, beta in PROBE:
        p = path(n, a, mm, beta, 0, 0)
        if not p.exists():
            continue
        inst = load(n, a)
        _, nrm = T.gso(np.load(p))
        pr = float(exact_F(nrm, [mm * inst["sigma"] ** 2])[0])
        rows.append((n, a, mm, beta, pr))
        print(f"n={n} alpha=0.{a} sigma={inst['sigma']:.1f} mm={mm} BKZ-{beta}: exact-law success at expected norm {100 * pr:.2f}%",
              flush=True)
    (HERE / "lwe_challenge_probe.json").write_text(json.dumps(rows))


def babai(B, t):
    """Babai nearest plane: lattice vector (integer row combination of B) near t."""
    Q, Rm = np.linalg.qr(B.astype(float).T)
    y = Q.T @ t.astype(float)
    c = np.zeros(len(B))
    for i in range(len(B) - 1, -1, -1):
        c[i] = np.rint((y[i] - Rm[i, i + 1:] @ c[i + 1:]) / Rm[i, i])
    return np.rint(c).astype(np.int64) @ B


def centred(x, q):
    x = x % q
    return np.where(x > q // 2, x - q, x)


def analyse():
    from scipy.stats import chi2
    out, X2, dof = {}, {"exact": 0.0, "independent": 0.0}, 0
    for n, a, mm, beta in SETTINGS:
        inst = load(n, a)
        q, sig, m = inst["q"], inst["sigma"], inst["m"]
        T_ = min(16, 1600 // mm)  # as in --reduce and R13 (13 and 11 instances); larger files keep extra samples unused
        bases = {}

        def get(t, j):
            if (t, j) not in bases:
                p = path(n, a, mm, beta, t, j)
                P = perm_for(n, a, mm, t, json.loads(p.with_suffix(".json").read_text())["perm_seed_j"])
                bases[(t, j)] = (np.load(p), P)
            return bases[(t, j)]

        def real_babai(t, j):
            At, bt = block(inst, mm, t)
            Bred, P = get(t, j)
            v = babai(Bred, bt[P]) % q
            s_hat = inv_mod(At[P][:n], q) @ v[:n] % q
            res = centred(inst["b"] - inst["A"] @ s_hat, q)
            return np.linalg.norm(res) < 2 * math.sqrt(m) * sig, s_hat, float(np.linalg.norm(res))

        # 1. find s with real Babai
        s, real = None, {}
        for t in range(T_):
            for j in range(K13):
                ok, s_hat, rn = real_babai(t, j)
                real[(t, j)] = ok
                if ok:
                    s = s_hat
                    print(f"  n={n} alpha=0.{a}: secret found by real Babai (block {t}, basis {j}); residual norm {rn:.1f}, "
                          f"expected about {math.sqrt(m) * sig:.1f}", flush=True)
                    break
            if s is not None:
                break
        if s is None:
            print(f"n={n} alpha=0.{a}: secret not found in {len(real)} real Babai runs; R13 cannot be evaluated", flush=True)
            out[f"{n},{a},{mm},{beta}"] = {"solved": False}
            continue
        e_all = centred(inst["b"] - inst["A"] @ s, q)
        # 64 more real-Babai checks after s is known
        extra = [(t, j) for t in range(T_) for j in range(K13) if (t, j) not in real][:64]
        for t, j in extra:
            real[(t, j)] = real_babai(t, j)[0]
        # 2. identity, models
        S, F, Pind = np.zeros((T_, K13), bool), np.zeros((T_, K13)), np.zeros((T_, K13))
        for t in range(T_):
            for j in range(K13):
                Bred, P = get(t, j)
                Bs, nrm = T.gso(Bred)
                o = e_all[t * mm:(t + 1) * mm][P].astype(float)
                S[t, j] = bool((np.abs((Bs / np.sqrt(nrm)[:, None]) @ o) < np.sqrt(nrm) / 2).all())
                F[t, j] = exact_F(nrm, [o @ o], M=100_000, seed=t * 1000 + j)[0]
                Pind[t, j] = prod_babai(nrm, mm * sig ** 2)
            bases.clear()
        mismatch = sum(S[t, j] != v for (t, j), v in real.items())
        assert mismatch == 0, f"projection identity disagrees with real Babai on {mismatch} of {len(real)}"
        counts = S.sum(1)
        norms = np.array([float((e_all[t * mm:(t + 1) * mm] ** 2).sum()) for t in range(T_)])
        rows = {}
        for name, Pm in (("exact", F), ("independent", Pind)):
            mu, var = Pm.sum(1), (Pm * (1 - Pm)).sum(1)
            z = (counts - mu) / np.sqrt(np.maximum(var, 1e-9))
            rows[name] = {"expected": mu.tolist(), "z": z.tolist(), "X2": float((z ** 2).sum())}
            X2[name] += float((z ** 2).sum())
        dof += T_
        rng = np.random.default_rng(13)
        stat, more = counts.var(), 0
        for _ in range(10_000):
            more += np.take_along_axis(S, rng.random(S.shape).argsort(0), 0).sum(1).var() >= stat
        key = f"{n},{a},{mm},{beta}"
        out[key] = {"solved": True, "instances": T_, "K": K13, "sigma": sig, "mean_success": float(S.mean()),
                    "counts": counts.tolist(), "norm_ratio": (norms / (mm * sig ** 2)).tolist(),
                    "real_babai_checks": len(real), "perm_p": (more + 1) / 10_001, "models": rows}
        print(f"n={n} alpha=0.{a} mm={mm} BKZ-{beta}: {T_} instances x {K13} attempts, success/attempt {S.mean():.3f}; "
              f"real-Babai checks {len(real)} (all agree); perm p {(more + 1) / 10_001:.4g}; "
              f"X2 exact {rows['exact']['X2']:.1f}, independent {rows['independent']['X2']:.1f} (dof {T_})", flush=True)
        for t in np.argsort(norms):
            print(f"    block {t:2d}: ||e||^2/(mm sigma^2) {norms[t] / (mm * sig ** 2):.3f}  count {counts[t]:2d}  "
                  f"exact {rows['exact']['expected'][t]:5.1f}  independent {rows['independent']['expected'][t]:5.1f}", flush=True)
    if dof:
        p_exact, p_ind = float(chi2.sf(X2["exact"], dof)), float(chi2.sf(X2["independent"], dof))
        out["verdict"] = {"X2": X2, "dof": dof, "p_exact": p_exact, "p_independent": p_ind,
                          "R13_pass": dof == 24 and p_exact > 0.01 and p_ind < 0.01}
        print("R13 verdict:", out["verdict"], flush=True)
    (HERE / "lwe_challenge_results.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--probe-predict", action="store_true")
    ap.add_argument("--reduce", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if a.probe:
        run_pool([(n, al, mm, beta, 0, 0) for n, al, mm, beta in PROBE], a.workers)
    if a.probe_predict:
        probe_predict()
    if a.reduce:
        jobs = [(n, al, mm, beta, t, j) for n, al, mm, beta in SETTINGS for t in range(min(16, 1600 // mm)) for j in range(K13)]
        run_pool(jobs, a.workers)
    if a.analyse:
        analyse()
