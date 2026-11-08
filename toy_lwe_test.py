"""Toy LWE test: do the list decoders help recover a planted secret?

Toy parameters only. No real ML-KEM keys, and nothing here is a security claim about ML-KEM.

Instance: b = A s + e mod q, q = 3329, m = n samples, s and e centered binomial (eta = 2 gives
sigma = 1). A is uniform. The lattice is {(y, x) : x = A y mod q}, dimension d = n + m, and the
target is (0, b). The lattice point (s, A s mod q) sits at offset (-s, e), so the noise has the
same size in every coordinate. Success means the decoder's point gives exactly s.

Unlike the earlier tests, the noise here is fixed and the basis comes from LLL or BKZ, so the
Gram-Schmidt profile has the shape a real attack sees. The planted point is far shorter than any
other, so the best possible recovery is 100%; there is no exact-CVP ceiling to estimate.

Rule, set before any run:
  Settings. For each reduction, two values of n picked from the pilot: "at the edge" (Babai closest
    to 50%) and "past Babai" (Babai at most 10%, some list decoder at least 10%; the largest such n).
  Selection. On tuning lattices, for each decoder family, the cheapest configuration in mean nodes
    within 3 points of the best recovery any family reaches there.
  Test. Scored once on held-out lattices with McNemar's exact test, Bonferroni-corrected across
    all comparisons in the table.
  Q1. Does the best list decoder recover significantly more secrets than Babai?
  Q2. VA-ANP adaptive "wins" against a baseline at a setting if it uses at least 1.5x fewer nodes
    with no significant loss of recovery. Baselines: Beam fixed list, Beam adaptive, per-level
    Lindner-Peikert. It passes only if it wins against all three at most settings.
  Exploratory, outside the rule: time per recovered secret against simply running stronger BKZ.

How it was run. Reduction needs fpylll (CPU only), so it runs in WSL, with the cache in a folder Windows
can read. Decoding then runs on the GPU from Windows, reading the cached bases.
  WSL:     export TOY_LWE_CACHE=/mnt/c/Users/<you>/toy_lwe_cache
           ~/toy_lwe_env/bin/python toy_lwe_test.py --check
           ~/toy_lwe_env/bin/python toy_lwe_test.py --pilot
           ~/toy_lwe_env/bin/python toy_lwe_test.py --reduce --settings "$S"
  Windows: uv run --no-project --python 3.12 --with numpy --with "torch==2.6.0+cu126"
             --index https://download.pytorch.org/whl/cu126 --index-strategy unsafe-best-match
             python toy_lwe_test.py --tune --gpu --workers 1 --budget 14400 --out toy_lwe_tune.json --settings "$S"
           (same command with --heldout --lattices 16 --budget 21600 --out toy_lwe_heldout.json)
  with S = [[2,70],[2,80],[10,80],[10,100],[20,90],[20,100]], the settings the pilot gave under the rule.
  Add --resume to continue a stopped stage. Results: toy_lwe_*_results.txt and toy_lwe_results.json.
"""
import argparse
import json
import math
import os
import pathlib
import sys
import time

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")  # each worker process stays on one core

from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import va_anp_v2 as V

Q = 3329
HERE = pathlib.Path(__file__).resolve().parent
CACHE = pathlib.Path(os.environ.get("TOY_LWE_CACHE", pathlib.Path.home() / "toy_lwe_cache"))
TAGS = {"check": 1, "pilot": 2, "tune": 3, "heldout": 4}


def cbd(rng, eta, size):
    """Centered binomial: difference of two sums of eta fair bits. Variance eta / 2."""
    return rng.binomial(eta, 0.5, size) - rng.binomial(eta, 0.5, size)


def make_A(tag, n, m, idx):
    # Doesn't depend on the reduction, so every reduction attacks the same instances.
    return np.random.default_rng([tag, n, m, idx, 0]).integers(0, Q, (m, n))


def make_targets(A, tag, eta, idx, count):
    n, m = A.shape[1], A.shape[0]
    rng = np.random.default_rng([tag, n, m, idx, eta, 1])
    out = []
    for _ in range(count):
        s, e = cbd(rng, eta, n), cbd(rng, eta, m)
        out.append((s, e, np.mod(A @ s + e, Q)))
    return out


def q_basis(A):
    n, m = A.shape[1], A.shape[0]
    B = np.zeros((n + m, n + m), dtype=np.int64)
    B[:n, :n] = np.eye(n, dtype=np.int64)
    B[:n, n:] = A.T
    B[n:, n:] = Q * np.eye(m, dtype=np.int64)
    return B


def reduce_basis(A, beta, time_limit):
    """LLL, then BKZ-beta if beta > 2. Returns the basis and how the reduction ended."""
    from fpylll import BKZ, LLL, IntegerMatrix

    B0 = q_basis(A)
    d = B0.shape[0]
    M = IntegerMatrix.from_matrix(B0.tolist())
    start = time.perf_counter()
    LLL.reduction(M)
    info = {"lll_s": time.perf_counter() - start, "beta": beta, "hit_limit": False}
    if beta > 2:
        p = BKZ.Param(block_size=beta, flags=BKZ.AUTO_ABORT | BKZ.MAX_LOOPS | BKZ.MAX_TIME,
                      max_loops=16, max_time=time_limit)
        # Double precision aborts with "infinite loop in babai" from about d = 200.
        BKZ.reduction(M, p, float_type="ld")
        info["hit_limit"] = time.perf_counter() - start >= time_limit
    info["reduce_s"] = time.perf_counter() - start
    return np.array([[M[i, j] for j in range(d)] for i in range(d)], dtype=np.int64), info


def reduced(tag, n, m, beta, idx, time_limit):
    """Reduced basis from the cache, or computed and cached. BKZ is by far the slowest step."""
    path = CACHE / f"t{tag}_n{n}_m{m}_b{beta}_i{idx}.npz"
    if path.exists():
        z = np.load(path)
        return z["B"], json.loads(str(z["info"]))
    B, info = reduce_basis(make_A(tag, n, m, idx), beta, time_limit)
    CACHE.mkdir(exist_ok=True)
    tmp = path.with_name(path.stem + f".{os.getpid()}.tmp.npz")
    np.savez(tmp, B=B, info=json.dumps(info))
    tmp.replace(path)
    return B, info


def gso(B):
    q, r = np.linalg.qr(B.astype(float).T)
    r = np.diag(r)
    return (q * r).T, r * r


def babai_formula(nrm, sigma):
    """Babai's success probability for Gaussian noise: the product of erf(||b*_i|| / (2 sqrt2 sigma))."""
    return math.exp(sum(math.log(max(math.erf(math.sqrt(x) / (2 * math.sqrt(2) * sigma)), 1e-300)) for x in nrm))


def run_cfg(cfg, B, Bs, nrm, t, sigma, lp_cache):
    """cap values are multiples of the lattice dimension d, so settings compare across n."""
    d = B.shape[0]
    kind = cfg[0]
    if kind == "babai":
        return V.babai(B, Bs, nrm, t)
    if kind == "beam":
        return V.beam(B, Bs, nrm, t, k=cfg[1], cap=cfg[2] * d)
    if kind == "beam_T":
        return V.beam(B, Bs, nrm, t, k=cfg[1], cap=cfg[3] * d, sigma=sigma, T=cfg[2])
    if kind == "anp":
        return V.anp(B, Bs, nrm, t, thr=cfg[1], cap=cfg[2] * d)
    if kind == "va":
        return V.va(B, Bs, nrm, t, sigma, llr=cfg[1], cap=cfg[2] * d)
    if kind == "va_T":
        return V.va(B, Bs, nrm, t, sigma, llr=cfg[1], cap=cfg[3] * d, T=cfg[2])
    if kind == "lp":
        if cfg not in lp_cache:
            lp_cache[cfg] = V.lp_planes(nrm, sigma, cfg[1])
        return V.lp(B, Bs, nrm, t, lp_cache[cfg])
    raise ValueError(cfg)


def is_lattice_point(point, A):
    """(y, x) is in the lattice exactly when x = A y mod q and all entries are integers."""
    n = A.shape[1]
    p = np.rint(point).astype(np.int64)
    return np.abs(point - p).max() < 1e-5 and np.array_equal(np.mod(A @ p[:n] - p[n:], Q), np.zeros(A.shape[0], int))


def run_job(job):
    """One lattice: reduce it, then run every decoder on every target."""
    tag, eta, n, m, beta, idx = (job[k] for k in ("tag", "eta", "n", "m", "beta", "idx"))
    sigma = math.sqrt(eta / 2)
    A = make_A(tag, n, m, idx)
    B, info = reduced(tag, n, m, beta, idx, job["time_limit"])
    Bs, nrm = gso(B)
    gs = np.sqrt(nrm)
    res = {str(c): {"got": [], "nodes": [], "children": [], "secs": []} for c in job["cfgs"]}
    closer_wrong = not_in_lattice = 0
    lp_cache = {}
    targets = make_targets(A, tag, eta, idx, job["targets"])
    ts = [np.concatenate([np.zeros(n, dtype=np.int64), b]) for *_, b in targets]
    for c in job["cfgs"]:
        if job.get("gpu"):
            import toy_lwe_gpu as G
            decoded = G.decode_all(c, B, Bs, nrm, np.stack(ts), sigma)
        else:
            decoded = [run_cfg(c, B, Bs, nrm, t, sigma, lp_cache) for t in ts]
        for (s, e, _), t, (point, secs, children, nodes) in zip(targets, ts, decoded):
            true_dist = int(s @ s + e @ e)
            got = np.array_equal(np.rint(point[:n]).astype(np.int64), s)
            r = res[str(c)]
            r["got"].append(bool(got))
            r["nodes"].append(int(nodes))
            r["children"].append(int(children))
            r["secs"].append(float(secs))
            closer_wrong += (not got) and float(((t - point) ** 2).sum()) <= true_dist
            not_in_lattice += not is_lattice_point(point, A)
    return {"tag": tag, "eta": eta, "n": n, "m": m, "beta": beta, "idx": idx, "info": info, "results": res,
            "gs_max": float(gs.max()), "gs_min": float(gs.min()), "gs_last": float(gs[-1]),
            "babai_formula": babai_formula(nrm, sigma), "closer_wrong": int(closer_wrong),
            "not_in_lattice": int(not_in_lattice)}


def run_jobs(jobs, workers, budget_s, label, on_done):
    """Runs jobs in parallel, prints a line per finished job and a heartbeat while waiting,
    and stops after budget_s so a stuck reduction can't hang the run silently."""
    start = time.perf_counter()
    out = []
    pool = ProcessPoolExecutor(workers)
    pending = {pool.submit(run_job, j): j for j in jobs}
    total = len(pending)
    print(f"[{label}] {total} jobs on {workers} workers", flush=True)
    try:
        while pending:
            done, _ = wait(pending, timeout=60, return_when=FIRST_COMPLETED)
            elapsed = time.perf_counter() - start
            for f in done:
                j = pending.pop(f)
                try:
                    r = f.result()
                except Exception as exc:  # report it and keep the other lattices
                    print(f"  FAILED n={j['n']} beta={j['beta']} idx={j['idx']}: {exc!r}", flush=True)
                    continue
                out.append(r)
                on_done(r, len(out), total, elapsed)
            if not done:
                print(f"  ... {elapsed:.0f}s, {len(pending)} of {total} jobs still running", flush=True)
            if elapsed > budget_s:
                print(f"  STOPPED at the {budget_s}s budget with {len(pending)} jobs unfinished", flush=True)
                for p in list(pool._processes.values()):
                    p.kill()
                break
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    return out


def beta_name(beta):
    return "LLL" if beta == 2 else f"BKZ-{beta}"


# ------------------------------------------------------------------ self-check

def self_check():
    from fpylll import CVP, GSO, LLL, IntegerMatrix

    rng = np.random.default_rng(11)

    x = cbd(rng, 2, 200000)
    assert abs(x.mean()) < 0.02 and abs(x.var() - 1.0) < 0.02 and x.min() >= -2 and x.max() <= 2
    print("  centered binomial eta=2: mean 0, variance 1, range -2..2", flush=True)

    tag = TAGS["check"]
    n = m = 30
    A = make_A(tag, n, m, 0)
    for s, e, b in make_targets(A, tag, 2, 0, 20):
        assert np.array_equal(np.mod(A @ s + e, Q), b)
    print("  b = A s + e mod q holds", flush=True)

    # The reduced basis must span the same lattice: same determinant, and every row in the lattice.
    for beta in (2, 10):
        B, _ = reduce_basis(A, beta, 120)
        Bs, nrm = gso(B)
        assert all(is_lattice_point(row.astype(float), A) for row in B)
        assert abs(0.5 * np.log(nrm).sum() - m * math.log(Q)) < 1e-6
        M = IntegerMatrix.from_matrix(B.tolist())
        G = GSO.Mat(M)
        G.update_gso()
        ref = np.array([G.get_r(i, i) for i in range(n + m)])
        assert np.allclose(ref, nrm, rtol=1e-6)
        print(f"  {beta_name(beta)}: basis spans the lattice, Gram-Schmidt matches fplll's", flush=True)

    cfgs = [("babai",), ("beam", 2, 2), ("beam", 3, 8), ("beam_T", 2, 8.0, 32), ("beam_T", 3, 16.0, 32),
            ("anp", 0.35, 2), ("va", 2.2, 2), ("va_T", 4.0, 16.0, 32), ("lp", 64)]

    # No noise: every decoder must return s exactly.
    Bs, nrm = gso(B)
    s = cbd(rng, 2, n)
    t = np.concatenate([np.zeros(n, dtype=np.int64), np.mod(A @ s, Q)])
    t_true = np.concatenate([s, np.mod(A @ s, Q)])
    for c in cfgs:
        point = run_cfg(c, B, Bs, nrm, t, 1.0, {})[0]
        # With e = 0 the true offset is (-s, 0), which is planted noise in y only.
        assert is_lattice_point(point, A), c
        assert ((t - point) ** 2).sum() <= ((t - t_true) ** 2).sum() + 1e-6, c
    print("  zero-error targets: all decoders return a lattice point at least as close as the true one", flush=True)

    # Independent exact CVP from fplll, on a small lattice with targets far from any lattice point.
    n2 = m2 = 12
    A2 = make_A(tag, n2, m2, 1)
    B2, _ = reduce_basis(A2, 2, 60)
    Bs2, nrm2 = gso(B2)
    M2 = IntegerMatrix.from_matrix(B2.tolist())
    LLL.reduction(M2)
    best_hits = 0
    runs = 30
    for _ in range(runs):
        t2 = np.concatenate([rng.integers(-Q, Q, n2), rng.integers(0, Q, m2)])
        exact = np.array(CVP.closest_vector(M2, tuple(int(v) for v in t2)), dtype=float)
        assert is_lattice_point(exact, A2)
        ed = ((t2 - exact) ** 2).sum()
        for c in cfgs:
            point = run_cfg(c, B2, Bs2, nrm2, t2, 1.0, {})[0]
            assert is_lattice_point(point, A2), c
            assert ((t2 - point) ** 2).sum() >= ed - 1e-6, f"{c} beat exact CVP"
        big = run_cfg(("beam", 3, 512), B2, Bs2, nrm2, t2, 1.0, {})[0]
        best_hits += abs(((t2 - big) ** 2).sum() - ed) < 1e-6
    print(f"  fplll exact CVP, dim 24: no decoder beat it on {runs} targets; "
          f"a large beam matched it on {best_hits}", flush=True)
    assert best_hits >= runs // 2

    # Negative control: uniform b has no planted secret, so nothing should look short.
    n3 = m3 = 50
    A3 = make_A(tag, n3, m3, 2)
    B3, _ = reduce_basis(A3, 2, 60)
    Bs3, nrm3 = gso(B3)
    planted = math.sqrt(n3 + m3)
    smallest = math.inf
    for _ in range(20):
        t3 = np.concatenate([np.zeros(n3, dtype=np.int64), rng.integers(0, Q, m3)])
        for c in cfgs:
            point = run_cfg(c, B3, Bs3, nrm3, t3, 1.0, {})[0]
            smallest = min(smallest, float(np.linalg.norm(t3 - point)))
    assert smallest > 2.5 * planted
    print(f"  negative control, uniform b: closest point found is at {smallest:.1f}, "
          f"a planted one would be near {planted:.1f}", flush=True)

    # Positive control: noise present, an easy setting, every decoder recovers everything.
    r = run_job({"tag": tag, "eta": 2, "n": 30, "m": 30, "beta": 2, "idx": 3, "targets": 20, "cfgs": cfgs,
                 "time_limit": 60})
    for c in cfgs:
        assert all(r["results"][str(c)]["got"]), f"{c} missed an easy target"
    assert r["closer_wrong"] == 0 and r["not_in_lattice"] == 0
    print(f"  easy instances, n=30 with LLL: every decoder recovers s on all 20 "
          f"(smallest Gram-Schmidt norm {r['gs_min']:.1f})", flush=True)
    print("  all checks passed", flush=True)


# ------------------------------------------------------------------ pilot

PILOT_CFGS = [("babai",), ("lp", 1024), ("beam", 2, 8), ("beam_T", 3, 16.0, 32), ("va_T", 4.0, 16.0, 32)]
PILOT_GRID = {2: range(40, 111, 10), 10: range(60, 151, 10), 20: range(80, 171, 10)}


def pilot(args):
    grid = PILOT_GRID if not args.grid else json.loads(args.grid)
    jobs = [{"tag": TAGS["pilot"], "eta": 2, "n": n, "m": n, "beta": int(beta), "idx": i, "targets": args.targets,
             "cfgs": PILOT_CFGS, "time_limit": args.time_limit}
            for beta, ns in grid.items() for n in ns for i in range(args.lattices)]
    jobs.sort(key=lambda j: (j["n"] * (1 + j["beta"]), j["idx"]))  # cheapest first, so results arrive early
    path = HERE / args.out
    out = json.loads(path.read_text()) if path.exists() and args.resume else []
    seen = {(r["n"], r["beta"], r["idx"]) for r in out}
    jobs = [j for j in jobs if (j["n"], j["beta"], j["idx"]) not in seen]

    def on_done(r, k, total, elapsed):
        out.append(r)
        path.write_text(json.dumps(out))
        hit = sum(r["results"][str(("babai",))]["got"])
        print(f"  [{k}/{total}] {elapsed:5.0f}s  {beta_name(r['beta']):<7} n={r['n']:<4} lattice {r['idx']}  "
              f"reduced in {r['info']['reduce_s']:6.1f}s{' (time limit)' if r['info']['hit_limit'] else ''}  "
              f"Babai {hit}/{len(r['results'][str(('babai',))]['got'])}", flush=True)

    run_jobs(jobs, args.workers, args.budget, "pilot", on_done)
    pilot_table(out)


def pilot_table(rows):
    names = {str(("babai",)): "Babai", str(("lp", 1024)): "LP 1024", str(("beam", 2, 8)): "Beam 8d",
             str(("beam_T", 3, 16.0, 32)): "Beam3 T16", str(("va_T", 4.0, 16.0, 32)): "VA T16"}
    print("\nSecret recovered, %, with mean nodes. 'Formula' is Babai's predicted success.")
    print(f"{'reduction':<9}{'n':>5}{'d':>5}{'targets':>8}{'reduce s':>9}{'GS min':>8}{'Formula':>9}"
          + "".join(f"{v:>18}" for v in names.values()))
    bad = sum(r["closer_wrong"] + r["not_in_lattice"] for r in rows)
    for beta in sorted({r["beta"] for r in rows}):
        for n in sorted({r["n"] for r in rows if r["beta"] == beta}):
            rs = [r for r in rows if r["beta"] == beta and r["n"] == n]
            count = sum(len(r["results"][str(("babai",))]["got"]) for r in rs)
            line = (f"{beta_name(beta):<9}{n:>5}{2 * n:>5}{count:>8}{np.mean([r['info']['reduce_s'] for r in rs]):>9.1f}"
                    f"{np.mean([r['gs_min'] for r in rs]):>8.2f}{100 * np.mean([r['babai_formula'] for r in rs]):>9.1f}")
            for key in names:
                got = [g for r in rs for g in r["results"][key]["got"]]
                nodes = [g for r in rs for g in r["results"][key]["nodes"]]
                line += f"{100 * np.mean(got):>8.1f}{np.mean(nodes):>10.0f}"
            print(line, flush=True)
    print(f"\nWrong points closer than the true one, plus points outside the lattice: {bad}", flush=True)


# ------------------------------------------------------------------ tuning and held-out

TS = (2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0, 32.0)
FAMILIES = {
    "Babai": [("babai",)],
    "Beam fixed list": [("beam", 2, c) for c in (1, 2, 4, 8, 16, 32, 64)],
    "Beam k=3 fixed list": [("beam", 3, c) for c in (1, 2, 4, 8, 16, 32, 64)],
    "ANP fixed list": [("anp", thr, c) for thr in (0.2, 0.35, 0.5, 0.7, 0.85) for c in (2, 8, 32)],
    "VA-ANP fixed list": [("va", llr, c) for llr in (1.0, 2.2, 4.0, 8.0) for c in (2, 8, 32)],
    "Beam adaptive": [("beam_T", 2, T, 64) for T in TS],
    "Beam k=3 adaptive": [("beam_T", 3, T, 64) for T in TS],
    "VA-ANP adaptive": [("va_T", llr, T, 64) for llr in (2.2, 4.0, 8.0) for T in TS],
    "LP per-level": [("lp", 2 ** k) for k in range(2, 17, 2)],
}
ALL_CFGS = [c for cfgs in FAMILIES.values() for c in cfgs]
BASELINES = ("Beam fixed list", "Beam adaptive", "LP per-level")
MARGIN = 3.0  # points below the best tuning recovery
RULE_RATIO = 1.5


def mcnemar(a, b):
    """Exact two-sided test on the targets where exactly one of two decoders recovered s."""
    x, y = int((a & ~b).sum()), int((~a & b).sum())
    n = x + y
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(min(x, y) + 1)) / 2 ** n) if n else 1.0
    return x, y, p


def tally(rows, beta, n, cfg):
    """Per-target arrays for one configuration at one setting, in a fixed lattice order."""
    key = str(cfg)
    rs = sorted((r for r in rows if r["beta"] == beta and r["n"] == n and key in r["results"]), key=lambda r: r["idx"])
    return {"got": np.array([g for r in rs for g in r["results"][key]["got"]], bool),
            "nodes": np.array([g for r in rs for g in r["results"][key]["nodes"]], float),
            "secs": np.array([g for r in rs for g in r["results"][key]["secs"]], float),
            "lat": np.array([r["idx"] for r in rs for _ in r["results"][key]["got"]])}


def cluster_boot(a, b, reps=2000):
    """95% intervals for recovery(a) - recovery(b) in points and nodes(b) / nodes(a), resampling
    whole lattices, because targets on one lattice aren't independent."""
    ids = np.unique(a["lat"])
    idx = [np.flatnonzero(a["lat"] == k) for k in ids]
    diff = np.array([a["got"][m].sum() - b["got"][m].sum() for m in idx], float)
    count = np.array([len(m) for m in idx], float)
    na = np.array([a["nodes"][m].sum() for m in idx], float)
    nb = np.array([b["nodes"][m].sum() for m in idx], float)
    pick = np.random.default_rng(0).integers(0, len(ids), (reps, len(ids)))
    d = 100 * diff[pick].sum(1) / count[pick].sum(1)
    r = nb[pick].sum(1) / na[pick].sum(1)
    return [float(v) for v in (*np.percentile(d, [2.5, 97.5]), *np.percentile(r, [2.5, 97.5]))]


def choose(rows, beta, n):
    """Selection from tuning data only: each family's cheapest configuration near the best recovery."""
    stats = {}
    for c in ALL_CFGS:
        t = tally(rows, beta, n, c)
        stats[c] = (100 * t["got"].mean(), t["nodes"].mean())
    best = max(v[0] for v in stats.values())
    target = best - MARGIN
    picks = {}
    for fam, cfgs in FAMILIES.items():
        ok = [c for c in cfgs if stats[c][0] >= target - 1e-9]
        picks[fam] = min(ok, key=lambda c: stats[c][1]) if ok else None
    # Q1 compares Babai with the list decoder that recovered the most on tuning data.
    lists = [c for c in ALL_CFGS if c != ("babai",)]
    strongest = max(lists, key=lambda c: (stats[c][0], -stats[c][1]))
    return {"best": best, "target": target, "picks": picks, "strongest": strongest,
            "tune": {str(c): stats[c] for c in ALL_CFGS}}


def lwe_jobs(stage, settings, cfgs_for, lattices, targets, time_limit):
    jobs = []
    for beta, n in settings:
        for i in range(lattices):
            jobs.append({"tag": TAGS[stage], "eta": 2, "n": n, "m": n, "beta": beta, "idx": i, "targets": targets,
                         "cfgs": cfgs_for(beta, n), "time_limit": time_limit})
    jobs.sort(key=lambda j: (j["n"] * (1 + j["beta"]), j["idx"]))
    return jobs


def run_stage(stage, jobs, args, path):
    out = json.loads(path.read_text()) if path.exists() and args.resume else []
    seen = {(r["n"], r["beta"], r["idx"]) for r in out}
    todo = [dict(j, gpu=args.gpu) for j in jobs if (j["n"], j["beta"], j["idx"]) not in seen]

    def on_done(r, k, total, elapsed):
        out.append(r)
        path.write_text(json.dumps(out))
        print(f"  [{k}/{total}] {elapsed:5.0f}s  {beta_name(r['beta']):<7} n={r['n']:<4} lattice {r['idx']:<3} "
              f"reduced in {r['info']['reduce_s']:6.1f}s{' (time limit)' if r['info']['hit_limit'] else ''}", flush=True)

    run_jobs(todo, args.workers, args.budget, stage, on_done)
    return out


def stronger(settings):
    """Exploratory: the same n under the stronger reductions, for Babai against list decoding."""
    betas = sorted({b for b, _ in settings})
    return sorted({(b2, n) for b, n in settings for b2 in betas if b2 > b} - set(settings))


def reduce_stage(args):
    """BKZ only, on the CPU in WSL. The bases go in the cache for the GPU decoding run."""
    settings = [tuple(s) for s in json.loads(args.settings)]
    jobs = (lwe_jobs("tune", settings, lambda b, n: [], args.tune_lattices, 0, args.time_limit)
            + lwe_jobs("heldout", settings + stronger(settings), lambda b, n: [], args.lattices, 0, args.time_limit))
    print(f"Reducing {len(jobs)} lattices into {CACHE}", flush=True)

    def on_done(r, k, total, elapsed):
        print(f"  [{k}/{total}] {elapsed:5.0f}s  tag {r['tag']} {beta_name(r['beta']):<7} n={r['n']:<4} lattice {r['idx']:<3} "
              f"reduced in {r['info']['reduce_s']:6.1f}s{' (time limit)' if r['info']['hit_limit'] else ''}", flush=True)

    done = run_jobs(jobs, args.workers, args.budget, "reduce", on_done)
    print(f"{len(done)} of {len(jobs)} lattices reduced", flush=True)


def tune_stage(args):
    settings = [tuple(s) for s in json.loads(args.settings)]
    jobs = lwe_jobs("tune", settings, lambda b, n: ALL_CFGS, args.tune_lattices, args.targets, args.time_limit)
    rows = run_stage("tune", jobs, args, HERE / args.out)
    for beta, n in settings:
        ch = choose(rows, beta, n)
        print(f"\n{beta_name(beta)} n={n}: best tuning recovery {ch['best']:.1f}%, target {ch['target']:.1f}%")
        for fam, c in ch["picks"].items():
            line = "cannot reach the target" if c is None else f"{str(c):<26}{ch['tune'][str(c)][0]:6.1f}% {ch['tune'][str(c)][1]:10.0f} nodes"
            print(f"  {fam:<22}{line}", flush=True)


def heldout_stage(args):
    settings = [tuple(s) for s in json.loads(args.settings)]
    tune = json.loads((HERE / args.tune_file).read_text())
    chosen = {s: choose(tune, *s) for s in settings}

    def cfgs_for(beta, n):
        ch = chosen[(beta, n)]
        cfgs = {("babai",), ch["strongest"]} | {c for c in ch["picks"].values() if c is not None}
        return sorted(cfgs, key=str)

    jobs = lwe_jobs("heldout", settings, cfgs_for, args.lattices, args.targets, args.time_limit)
    jobs += lwe_jobs("heldout", stronger(settings), lambda b, n: [("babai",)], args.lattices, args.targets, args.time_limit)
    rows = run_stage("heldout", jobs, args, HERE / args.out)

    alpha = 0.05 / (len(settings) * (1 + len(BASELINES)))
    print(f"\nBonferroni alpha: {alpha:.5f} ({len(settings)} settings x {1 + len(BASELINES)} comparisons)")
    report = []
    for s in settings:
        beta, n = s
        ch = chosen[s]
        block = {"beta": beta, "n": n, "best_tune": ch["best"], "target": ch["target"], "families": {},
                 "strongest": str(ch["strongest"])}
        rs = [r for r in rows if r["beta"] == beta and r["n"] == n]
        block["bad_points"] = sum(r["closer_wrong"] + r["not_in_lattice"] for r in rs)
        block["reduce_s"] = float(np.mean([r["info"]["reduce_s"] for r in rs]))
        block["hit_limit"] = sum(r["info"]["hit_limit"] for r in rs)
        block["gs_min"] = float(np.mean([r["gs_min"] for r in rs]))
        babai = tally(rows, beta, n, ("babai",))
        block["targets"] = len(babai["got"])
        block["babai"] = float(100 * babai["got"].mean())
        block["babai_formula"] = float(100 * np.mean([r["babai_formula"] for r in rs]))
        print(f"\n=== {beta_name(beta)} n={n} (d={2 * n}), {len(babai['got'])} held-out targets, Babai {block['babai']:.1f}% "
              f"(formula {block['babai_formula']:.1f}%), reduction {block['reduce_s']:.1f}s, target on tuning {ch['target']:.1f}%")
        for fam, c in ch["picks"].items():
            if c is None:
                block["families"][fam] = None
                print(f"  {fam:<22}cannot reach the target on tuning data")
                continue
            t = tally(rows, beta, n, c)
            block["families"][fam] = {"cfg": str(c), "tune": ch["tune"][str(c)][0], "held_out": float(100 * t["got"].mean()),
                                      "nodes": float(t["nodes"].mean()), "ms": float(1000 * t["secs"].mean())}
            f = block["families"][fam]
            print(f"  {fam:<22}{str(c):<26}tune {f['tune']:5.1f}%  held-out {f['held_out']:5.1f}%  "
                  f"{f['nodes']:10.0f} nodes  {f['ms']:9.1f} ms", flush=True)

        strong = tally(rows, beta, n, ch["strongest"])
        x, y, p = mcnemar(strong["got"], babai["got"])
        lo, hi, _, _ = cluster_boot(strong, babai)
        block["q1"] = {"cfg": str(ch["strongest"]), "strongest": float(100 * strong["got"].mean()), "only_list": x, "only_babai": y,
                       "p": p, "diff_ci": [lo, hi], "gain": bool(x > y and p < alpha), "nodes": float(strong["nodes"].mean())}
        print(f"  Q1 strongest list {ch['strongest']}: {100 * strong['got'].mean():.1f}% vs Babai {block['babai']:.1f}%, "
              f"only list/only Babai {x}/{y}, p={p:.2g}, diff CI {lo:+.1f} to {hi:+.1f} => "
              f"{'significant gain' if block['q1']['gain'] else 'no significant gain'}")

        block["q2"] = {}
        va_cfg = ch["picks"]["VA-ANP adaptive"]
        for base in BASELINES:
            bc = ch["picks"][base]
            if va_cfg is None:
                block["q2"][base] = {"win": False, "why": "VA-ANP adaptive cannot reach the target"}
            elif bc is None:
                block["q2"][base] = {"win": True, "why": "baseline cannot reach the target"}
            else:
                a, b = tally(rows, beta, n, va_cfg), tally(rows, beta, n, bc)
                x, y, p = mcnemar(b["got"], a["got"])
                lo, hi, rlo, rhi = cluster_boot(a, b)
                ratio = float(b["nodes"].sum() / a["nodes"].sum())
                loss = bool(x > y and p < alpha)
                block["q2"][base] = {"ratio": ratio, "ratio_ci": [rlo, rhi], "base_only": x, "va_only": y, "p": p,
                                     "diff_ci": [lo, hi], "significant_loss": loss, "win": bool(ratio >= RULE_RATIO and not loss)}
            q = block["q2"][base]
            if "ratio" in q:
                print(f"  Q2 vs {base:<16} nodes {q['ratio']:.2f}x (CI {q['ratio_ci'][0]:.2f}-{q['ratio_ci'][1]:.2f}), "
                      f"baseline-only/VA-only {q['base_only']}/{q['va_only']}, p={q['p']:.2g} => {'WIN' if q['win'] else 'no win'}")
            else:
                print(f"  Q2 vs {base:<16} {q['why']} => {'WIN' if q['win'] else 'no win'}")
        block["q2_all_three"] = all(block["q2"][b]["win"] for b in BASELINES)
        report.append(block)

    wins = sum(b["q2_all_three"] for b in report)
    passed = wins > len(report) / 2
    print(f"\nQ2 verdict: VA-ANP adaptive wins against all three baselines at {wins} of {len(report)} settings "
          f"=> rule {'PASSED' if passed else 'FAILED'}")
    q1 = sum(b["q1"]["gain"] for b in report)
    print(f"Q1 verdict: a list decoder recovers significantly more than Babai at {q1} of {len(report)} settings")

    # Exploratory: time per recovered secret, list decoding against stronger reduction on the same n.
    print("\nExploratory, not in the rule: seconds per recovered secret = (reduction + decoding) / recovery.")
    print("Reduction and decoding times were measured while other jobs shared the machine.")
    effort = []
    for n in sorted({n for _, n in settings}):
        for beta in sorted({r["beta"] for r in rows if r["n"] == n}):
            rs = [r for r in rows if r["beta"] == beta and r["n"] == n]
            red = float(np.mean([r["info"]["reduce_s"] for r in rs]))
            ch = chosen.get((beta, n))
            options = {"Babai": ("babai",)}
            if ch:
                for fam in ("Beam adaptive", "Beam k=3 adaptive", "VA-ANP adaptive", "LP per-level"):
                    if ch["picks"][fam]:
                        options[fam] = ch["picks"][fam]
                options["Strongest list"] = ch["strongest"]
            for name, c in options.items():
                t = tally(rows, beta, n, c)
                p = float(t["got"].mean())
                sec = (red + float(t["secs"].mean())) / p if p else None
                effort.append({"n": n, "beta": beta, "decoder": name, "cfg": str(c), "recovery": 100 * p, "reduce_s": red,
                               "decode_s": float(t["secs"].mean()), "sec_per_secret": sec})
                print(f"  n={n:<4}{beta_name(beta):<8}{name:<20}{100 * p:6.1f}%  reduce {red:8.1f}s  "
                      f"decode {t['secs'].mean():8.3f}s  {'no recoveries' if sec is None else f'{sec:9.1f}s per secret'}", flush=True)

    summary = {"settings": report, "alpha": alpha, "q1_gains": q1, "q2_wins": wins, "rule_passed": passed, "effort": effort,
               "bad_points": sum(r["closer_wrong"] + r["not_in_lattice"] for r in rows)}
    (HERE / "toy_lwe_results.json").write_text(json.dumps(summary, indent=1))
    print(f"\nWrong points closer than the true one, plus points outside the lattice: {summary['bad_points']}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--reduce", action="store_true", help="BKZ only, for tuning and held-out lattices")
    ap.add_argument("--tune", action="store_true")
    ap.add_argument("--heldout", action="store_true")
    ap.add_argument("--gpu", action="store_true", help="decode on the GPU; use with --workers 1")
    ap.add_argument("--tune-lattices", type=int, default=6)
    ap.add_argument("--table", action="store_true", help="reprint the pilot table from saved results")
    ap.add_argument("--grid", default="", help='JSON such as {"2": [60, 65]}')
    ap.add_argument("--settings", default="", help="JSON list of [beta, n], such as [[2, 70], [10, 100]]")
    ap.add_argument("--lattices", type=int, default=4)
    ap.add_argument("--targets", type=int, default=25)
    ap.add_argument("--workers", type=int, default=18)
    ap.add_argument("--time-limit", type=int, default=900, help="seconds for one BKZ run")
    ap.add_argument("--budget", type=int, default=2400, help="seconds for the whole stage")
    ap.add_argument("--out", default="toy_lwe_pilot.json")
    ap.add_argument("--tune-file", default="toy_lwe_tune.json")
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    if a.check:
        self_check()
    if a.pilot:
        pilot(a)
    if a.reduce:
        reduce_stage(a)
    if a.tune:
        tune_stage(a)
    if a.heldout:
        heldout_stage(a)
    if a.table:
        pilot_table(json.loads((HERE / a.out).read_text()))
