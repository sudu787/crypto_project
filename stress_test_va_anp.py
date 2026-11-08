"""Stress test of the VA-ANP claim in CVP_VA_ANP_Comparison.ipynb.

Loads the decoder functions straight from the notebook (unmodified) and runs:
  0  check GPU LLL against the notebook and reproduce its saved seed-42 result
  A  10 fresh seeds, paired VA-ANP vs ANP, plus exact CVP to find the real ceiling
  B  VA-ANP given a wrong sigma
  C  threshold tuning on one set, scored on a held-out set; what each VA-ANP part adds
  D  larger dimensions
  E  low noise and non-Gaussian (scaled centered binomial) noise
Add --v2 for the fair benchmark, --v2-noise to retune per noise level, --v2-planes for the dim 40 test.

Needs an NVIDIA GPU. Run:
  uv run --no-project --python 3.12 --with numpy --with "torch==2.6.0+cu126"
    --index https://download.pytorch.org/whl/cu126 --index-strategy unsafe-best-match
    python stress_test_va_anp.py
"""
import json
import math
import os
import platform
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
from numpy.linalg import norm

import va_anp_v2 as V

NB =Path(__file__).with_name("CVP_VA_ANP_Comparison.ipynb")
ns = {"np": np, "norm": norm, "time": time}
for cell in json.loads(NB.read_text(encoding="utf8"))["cells"]:
    src = "".join(cell["source"])
    if cell["cell_type"] == "code" and "def " in src and "run_head_to_head" not in src:
        exec(src, ns)

generate_qary_lattice = ns["generate_qary_lattice"]
lll_reduce = ns["lll_reduce"]
generate_bdd_instance = ns["generate_bdd_instance"]
babai_np = ns["babai_nearest_plane"]
lp_fixed = ns["code2_lp_fixed"]
lp_orig = ns["code1_lp_original"]
anp = ns["code1_anp_fractional"]
va = ns["code2_variance_aware_anp"]

Q = 3329
DIMS = [10, 12, 14, 16]
RATIOS = [0.18, 0.24, 0.30]
OFF = 1e18  # disables an LLR or sphere check


class _NodeLimit(Exception):
    pass


def exact_cvp(B, B_star, nrm_sq, target, start_point, limit=None):
    """Schnorr-Euchner enumeration; returns the true closest lattice point.
    With limit set, returns None if the search visits more than that many nodes."""
    best = [float(np.dot(target - start_point, target - start_point)) + 1e-9, start_point]
    n = B.shape[0]
    visited = [0]

    def rec(i, b, acc):
        visited[0] += 1
        if limit is not None and visited[0] > limit:
            raise _NodeLimit
        if i < 0:
            if acc < best[0]:
                best[0], best[1] = acc, target - b
            return
        c = float(np.dot(b, B_star[i]) / nrm_sq[i])
        m0 = round(c)
        step = 1 if c >= m0 else -1
        off = 0
        misses = 0
        while misses < 2:  # zig-zag; stop once both sides exceed the radius
            for m in ([m0] if off == 0 else [m0 + step * off, m0 - step * off]):
                d = acc + (c - m) ** 2 * nrm_sq[i]
                if d < best[0]:
                    rec(i - 1, b - m * B[i], d)
                else:
                    misses += 1
            if off == 0:
                misses = 0
            elif misses < 2:
                misses = 0
            off += 1

    try:
        rec(n - 1, target.astype(float).copy(), 0.0)
    except _NodeLimit:
        return None
    return best[1]


def gpu_lll(raws, delta=0.99):
    """Batched GPU version of the notebook's lll_reduce, with the same step order.
    exp0 asserts that it matches lll_reduce and reproduces the notebook's results."""
    import torch  # imported here so the exact-CVP worker processes don't load it

    def gs(A):
        Bs, nrm = torch.zeros_like(A), torch.zeros(A.shape[:2], dtype=A.dtype, device=A.device)
        mu = torch.zeros_like(A)
        for i in range(A.shape[1]):
            v = A[:, i]
            if i:
                mu[:, i, :i] = (A[:, i, None] * Bs[:, :i]).sum(-1) / nrm[:, :i]
                v = v - (mu[:, i, :i, None] * Bs[:, :i]).sum(1)
            Bs[:, i] = v
            nrm[:, i] = (v * v).sum(-1)
        return Bs, mu, nrm

    def gs_fast(A):  # same mu and norms via one QR call, far fewer Python-level GPU operations
        L = torch.linalg.qr(A.transpose(1, 2), mode="r")[1].transpose(1, 2)
        d = torch.diagonal(L, dim1=1, dim2=2)
        return torch.tril(L / d[:, None, :], -1), d * d

    # Measured at dim 16: GPU about 10 ms/step at any batch size; CPU 2.2 ms at 90, 17 ms at 900.
    # So the crossover is near 500 lattices there; QR cost grows as n^3, so scale it (estimate).
    dev = "cuda" if len(raws) * raws[0].shape[0] ** 3 >= 2_000_000 else "cpu"
    t0 = time.time()
    B = torch.tensor(np.stack(raws), dtype=torch.float64, device=dev)
    N, n = B.shape[:2]
    k = torch.ones(N, dtype=torch.long, device=dev)
    active = torch.arange(N, device=dev)
    # Each j gets one visit per pass, as in the notebook. Without this, a true mu = +-0.5 tie
    # flips sign on float noise and size-reduction never ends.
    cur = k - 1
    cols = torch.arange(n, device=dev)[None]
    steps = 0
    while active.numel():
        steps += 1
        if steps > 2_000_000:
            raise RuntimeError(f"LLL did not terminate: {active.numel()} lattices left")
        A = B[active]
        mu, nrm = gs_fast(A)
        ka, idx = k[active], torch.arange(active.numel(), device=dev)
        row = mu[idx, ka]
        big = (row.abs() > 0.5) & (cols <= cur[active][:, None])
        has = big.any(1)
        top = n - 1 - big.flip(1).float().argmax(1)  # highest j with |mu[k,j]| > 0.5
        s, j = idx[has], top[has]
        A[s, ka[s]] -= torch.round(row[s, j])[:, None] * A[s, j]  # size-reduce one step
        cur[active[s]] = j - 1

        rest, kr = idx[~has], ka[~has]
        ok = nrm[rest, kr] >= (delta - mu[rest, kr, kr - 1] ** 2) * nrm[rest, kr - 1]
        k[active[rest[ok]]] += 1
        sw, ks = rest[~ok], kr[~ok]
        tmp = A[sw, ks].clone()
        A[sw, ks] = A[sw, ks - 1]
        A[sw, ks - 1] = tmp
        k[active[sw]] = (ks - 1).clamp(min=1)
        moved = active[rest]
        cur[moved] = k[moved] - 1

        B[active] = A
        active = active[k[active] < n]
    Bs, _, nrm = gs(B)
    print(f"    LLL dim={n} x{N} on {dev}: {time.time() - t0:.0f}s", flush=True)
    return [(b, s, r) for b, s, r in zip(B.cpu().numpy(), Bs.cpu().numpy(), nrm.cpu().numpy())]


def make_target(B, Bs, nrm, ratio):
    sigma = ratio * np.exp(0.5 * np.mean(np.log(nrm)))
    t, true = generate_bdd_instance(B, sigma)
    return dict(B=B, Bs=Bs, nrm=nrm, t=t, true=true, sigma=sigma,
                dim=B.shape[0], ratio=ratio)


def _exact(i):
    return exact_cvp(i["B"], i["Bs"], i["nrm"], i["t"], i["true"])


def bank(seeds, dims=DIMS, ratios=RATIOS, trials=30, noise="gauss"):
    # Draws random numbers in the notebook's order (lattice, coefficients, noise), so seed 42
    # gives the notebook's instances. Noise is drawn at sigma=1 and scaled after LLL.
    raw = []
    for s in seeds:
        np.random.seed(s)
        for d in dims:
            for r in ratios:
                for _ in range(trials):
                    L = generate_qary_lattice(d, Q)
                    coef = np.random.randint(-3, 4, size=d)
                    if noise == "gauss":
                        z = np.random.normal(0.0, 1.0, size=d)
                    else:  # centered binomial eta=3, scaled to unit variance
                        z = (np.random.randint(0, 2, (d, 3)).sum(1)
                             - np.random.randint(0, 2, (d, 3)).sum(1)) / math.sqrt(1.5)
                    raw.append((s, d, r, L, coef, z))
    reduced = {d: iter(gpu_lll([x[3] for x in raw if x[1] == d])) for d in dims}
    out = []
    for s, d, r, _, coef, z in raw:
        B, Bs, nrm = next(reduced[d])
        sigma = r * np.exp(0.5 * np.mean(np.log(nrm)))
        true = coef @ B
        out.append(dict(B=B, Bs=Bs, nrm=nrm, t=true + sigma * z, true=true, sigma=sigma,
                        dim=d, ratio=r, seed=s))
    return out


def run_va(inst, sigma_mult=1.0, llr=2.2, sphere=2.8):
    v, t, st = va(inst["B"], inst["Bs"], inst["nrm"], inst["t"], inst["sigma"] * sigma_mult,
                  llr_threshold=llr, sphere_mult=sphere)
    return v, t, st["children"], st["nodes"]


def run_anp(inst, thr=0.35):
    v, t, st = anp(inst["B"], inst["Bs"], inst["nrm"], inst["t"], thr)
    return v, t, st["children"], st["nodes"]


def run_np(inst):
    v, t = babai_np(inst["B"], inst["Bs"], inst["nrm"], inst["t"])
    return v, t, inst["dim"], inst["dim"]


def run_lp2(inst):
    v, t = lp_fixed(inst["B"], inst["Bs"], inst["nrm"], inst["t"], num_planes=2)
    return v, t, None, None


def evaluate(algos, insts):
    """Run every algorithm on every instance, in shuffled order for fair timing."""
    res = {k: dict(ok=[], t=[], ch=0, nd=0, v=[]) for k in algos}
    names = list(algos)
    rng = random.Random(1)
    for inst in insts:
        rng.shuffle(names)
        for k in names:
            v, t, ch, nd = algos[k](inst)
            r = res[k]
            r["ok"].append(norm(v - inst["true"]) < 1e-3)
            r["t"].append(t)
            r["v"].append(v)
            r["ch"] += ch or 0
            r["nd"] += nd or 0
    for r in res.values():
        r["ok"] = np.array(r["ok"])
        r["t"] = np.array(r["t"])
    return res


def line(name, r):
    planes = f"{r['ch'] / r['nd']:5.2f}" if r["nd"] else "    -"
    print(f"  {name:<30} {r['ok'].mean() * 100:6.1f}%  {r['t'].mean() * 1000:7.3f} ms  {planes}", flush=True)


def mcnemar(a, b):
    x, y = int((a & ~b).sum()), int((~a & b).sum())
    n = x + y
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(min(x, y) + 1)) / 2 ** n) if n else 1.0
    return x, y, p


def exp0():
    print("\n[0] Reproduce notebook (seed 42) - exact counts must be 253 / 252", flush=True)
    np.random.seed(7)
    for d in DIMS:  # GPU LLL must give the same basis as the notebook's lll_reduce
        L = generate_qary_lattice(d, Q)
        assert np.allclose(gpu_lll([L])[0][0], lll_reduce(L)[0], atol=1e-6), f"LLL differs at dim {d}"
    print("  GPU LLL matches notebook lll_reduce", flush=True)
    insts = bank([42])
    a = sum(norm(run_anp(i)[0] - i["true"]) < 1e-3 for i in insts)
    v_ = sum(norm(run_va(i)[0] - i["true"]) < 1e-3 for i in insts)
    print(f"  ANP {a}/360, VA-ANP {v_}/360", flush=True)
    assert (a, v_) == (253, 252), "harness does not match the notebook"


def expA():
    print("\n[A] 10 fresh seeds, 3600 paired instances", flush=True)
    insts = bank(range(10))
    res = evaluate({"Babai-NP": run_np, "LP k=2": run_lp2, "ANP (0.35)": run_anp, "VA-ANP": run_va}, insts)
    for k, r in res.items():
        line(k, r)
    a, v = res["ANP (0.35)"], res["VA-ANP"]
    x, y, p = mcnemar(a["ok"], v["ok"])
    print(f"  ANP-only wins {x}, VA-only wins {y}, McNemar p={p:.4f}")
    print(f"  overall speedup {a['t'].sum() / v['t'].sum():.2f}x")

    seeds = np.array([i["seed"] for i in insts])
    per = [a["t"][seeds == s].sum() / v["t"][seeds == s].sum() for s in range(10)]
    gap = [(a["ok"][seeds == s].mean() - v["ok"][seeds == s].mean()) * 100 for s in range(10)]
    print(f"  speedup per seed min/median/max {min(per):.2f}/{np.median(per):.2f}/{max(per):.2f}")
    print(f"  accuracy gap (ANP-VA) per seed min/median/max {min(gap):+.2f}/{np.median(gap):+.2f}/{max(gap):+.2f} pts")

    dims, ratios = np.array([i["dim"] for i in insts]), np.array([i["ratio"] for i in insts])
    for label, arr, vals in (("dim", dims, DIMS), ("noise", ratios, RATIOS)):
        for val in vals:
            m = arr == val
            print(f"  {label}={val}: speedup {a['t'][m].sum() / v['t'][m].sum():.2f}x, "
                  f"ANP {a['ok'][m].mean() * 100:.1f}% VA {v['ok'][m].mean() * 100:.1f}% "
                  f"Babai {res['Babai-NP']['ok'][m].mean() * 100:.1f}%")

    print("\n  Exact CVP (is the ceiling real?)", flush=True)
    sols = list(POOL.map(_exact, insts, chunksize=8))
    for k, r in res.items():  # no decoder may beat the exact solver
        for i, s, dec in zip(insts, sols, r["v"]):
            assert norm(i["t"] - s) <= norm(i["t"] - dec) + 1e-6, "enumeration is not exact"
    ceil = np.array([norm(s - i["true"]) < 1e-3 for s, i in zip(sols, insts)])
    print(f"  true point IS the closest point: {ceil.mean() * 100:.1f}%  <- ceiling for any decoder")
    for val in RATIOS:
        print(f"    noise={val}: {ceil[ratios == val].mean() * 100:.1f}%")
    for k, r in res.items():
        same = np.mean([norm(s - dec) < 1e-3 for s, dec in zip(sols, r["v"])]) * 100
        print(f"  {k:<14} returned the true closest point: {same:.1f}%")


def expB():
    print("\n[B] VA-ANP with wrong sigma (1080 instances)", flush=True)
    insts = bank(range(100, 103))
    algos = {f"sigma x {m}": (lambda i, m=m: run_va(i, sigma_mult=m))
             for m in (0.25, 0.5, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0, 4.0)}
    algos["ANP (0.35, needs no sigma)"] = run_anp
    res = evaluate(algos, insts)
    for k, r in res.items():
        line(k, r)


def expC():
    print("\n[C] Tune on one set, score on another (1080 each)", flush=True)
    tune, test = bank(range(200, 203)), bank(range(203, 206))
    an = {f"ANP thr={t}": (lambda i, t=t: run_anp(i, t))
          for t in (0.2, 0.35, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98)}
    vg = {f"VA llr={l} sph={s}": (lambda i, l=l, s=s: run_va(i, llr=l, sphere=s))
          for l in (0.5, 1.0, 1.5, 2.2, 3.0, 4.0) for s in (2.0, 2.8, 4.0)}
    abl = {"VA full (2.2, 2.8)": run_va,
           "VA LLR only (2.2, no sphere)": lambda i: run_va(i, sphere=OFF),
           "VA sphere only (no LLR, 2.8)": lambda i: run_va(i, llr=OFF),
           "VA neither": lambda i: run_va(i, llr=OFF, sphere=OFF)}

    print("  Curves on the tuning set:")
    rt = evaluate({**an, **vg, **abl}, tune)
    for k, r in rt.items():
        line(k, r)

    def pick(group):  # fastest config within 0.5 points of the group's best accuracy
        best = max(rt[k]["ok"].mean() for k in group)
        return min((k for k in group if rt[k]["ok"].mean() >= best - 0.005),
                   key=lambda k: rt[k]["t"].mean())

    pa, pv = pick(an), pick(vg)
    print(f"  Picked on tuning set: {pa} | {pv}")
    print("  Held-out test set:")
    final = {pa: an[pa], "ANP thr=0.35 (notebook)": run_anp, pv: vg[pv], "VA notebook (2.2, 2.8)": run_va}
    rf = evaluate(final, test)
    for k, r in rf.items():
        line(k, r)
    x, y, p = mcnemar(rf[pa]["ok"], rf[pv]["ok"])
    print(f"  tuned ANP vs tuned VA: ANP-only {x}, VA-only {y}, p={p:.4f}, "
          f"speedup {rf[pa]['t'].sum() / rf[pv]['t'].sum():.2f}x")


def expD():
    print("\n[D] Larger dimensions (6 lattices x 3 noises x 25 targets per dim)", flush=True)
    for d in (20, 24, 30, 40):
        np.random.seed(300 + d)
        t0 = time.time()
        insts = []
        for B, Bs, nrm in gpu_lll([generate_qary_lattice(d, Q) for _ in range(6)]):
            insts += [make_target(B, Bs, nrm, r) for r in RATIOS for _ in range(25)]
        print(f"  dim={d} (LLL {time.time() - t0:.0f}s)", flush=True)
        res = evaluate({"Babai-NP": run_np, "LP k=2": run_lp2, "ANP (0.35)": run_anp, "VA-ANP": run_va}, insts)
        for k, r in res.items():
            line(k, r)
        a, v = res["ANP (0.35)"], res["VA-ANP"]
        x, y, p = mcnemar(a["ok"], v["ok"])
        print(f"    speedup {a['t'].sum() / v['t'].sum():.2f}x; ANP-only {x}, VA-only {y}, p={p:.4f}", flush=True)


def expE():
    algos = {"Babai-NP": run_np, "ANP (0.35)": run_anp, "VA-ANP": run_va}
    print("\n[E1] Lower noise (360 per ratio); 0.02 is about ML-KEM-512's sigma of 1.22", flush=True)
    for r in (0.02, 0.06, 0.10, 0.14):
        res = evaluate(algos, bank([400], ratios=[r], trials=90))
        print(f"  ratio={r}")
        for k, v in res.items():
            line(k, v)
        print(f"    speedup {res['ANP (0.35)']['t'].sum() / res['VA-ANP']['t'].sum():.2f}x")
    print("\n[E2] Scaled centered binomial noise, eta=3 (1080)", flush=True)
    res = evaluate(algos, bank(range(500, 503), noise="cbd"))
    for k, v in res.items():
        line(k, v)
    print(f"    speedup {res['ANP (0.35)']['t'].sum() / res['VA-ANP']['t'].sum():.2f}x")


# ---------------------------------------------------------------------------------------------
# v2 benchmark: fair baselines, adaptive list, held-out scoring. Run with --v2.
# ---------------------------------------------------------------------------------------------
V2_DIMS = [16, 24, 30, 40]
V2_NOISE = [0.18, 0.24, 0.30]
V2_LATTICES = 60  # half tuning, half held-out, so scores never share a lattice with tuning
V2_TARGETS = 20  # per lattice, per noise level
V2_MARGINS = (0.01, 0.03)  # how far below the best tuning accuracy each comparison sits
V2_ALPHA = 0.05 / (2 * len(V2_NOISE))  # Bonferroni: dims 30 and 40 x noise levels
V2_RULE_RATIO = 1.5  # success rule, fixed before running: at least 1.5x fewer nodes
TS = (1, 2, 3, 4, 6, 8, 12)
EXACT_LIMIT = 2_000_000
FAMILIES = {"ANP fixed list": "anp", "Beam fixed list": "beam", "LP per-level": "lp",
            "VA-ANP fixed list": "va", "VA-ANP adaptive": "va_T",
            "ANP adaptive": "anp_T", "Beam adaptive": "beam_T"}


def v2_configs():
    """Every setting tried. Baselines tune their list size too, not only their threshold."""
    c = [("babai",)]
    c += [("anp", t, x) for t in (0.35, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95) for x in (1, 2, 4, 8)]
    c += [("beam", 2, x) for x in (0.5, 1, 2, 4, 8, 16)]
    c += [("lp", x) for x in (1, 2, 4, 8, 16, 32)]
    c += [("va", l, x) for l in (1.0, 1.5, 2.2, 3.0, 4.0) for x in (1, 2, 4, 8)]
    c += [("va_T", l, T) for l in (1.5, 2.2, 3.0, 4.0) for T in TS]
    c += [("anp_T", t, T) for t in (0.5, 0.7, 0.85) for T in TS]
    c += [("beam_T", T) for T in TS]
    return c


def run_cfg(cfg, i):
    B, Bs, nrm, t, s, n = i["B"], i["Bs"], i["nrm"], i["t"], i["sigma"], i["dim"]
    kind, safety = cfg[0], 32 * n  # safety only limits memory for the adaptive decoders
    if kind == "babai":
        return V.babai(B, Bs, nrm, t)
    if kind == "anp":
        return V.anp(B, Bs, nrm, t, thr=cfg[1], cap=int(cfg[2] * n))
    if kind == "beam":
        return V.beam(B, Bs, nrm, t, k=cfg[1], cap=int(cfg[2] * n))
    if kind == "lp":
        return V.lp(B, Bs, nrm, t, V.lp_planes(nrm, s, int(cfg[1] * n)))
    if kind == "va":
        return V.va(B, Bs, nrm, t, s, llr=cfg[1], cap=int(cfg[2] * n))
    if kind == "va_T":
        return V.va(B, Bs, nrm, t, s, llr=cfg[1], T=cfg[2], cap=safety)
    if kind == "anp_T":
        return V.anp(B, Bs, nrm, t, thr=cfg[1], T=cfg[2], cap=safety, sigma=s)
    if kind == "beam_T":
        return V.beam(B, Bs, nrm, t, k=2, T=cfg[1], cap=safety, sigma=s)
    if kind == "beam3_T":
        return V.beam(B, Bs, nrm, t, k=3, T=cfg[1], cap=safety, sigma=s)
    raise ValueError(kind)


def _init_worker(insts):
    global _INST
    _INST = insts


def _cfg_job(cfg):
    out = [run_cfg(cfg, i) for i in _INST]
    return cfg, dict(
        ok=np.array([norm(r[0] - i["true"]) < 1e-3 for r, i in zip(out, _INST)]),
        dist=np.array([norm(i["t"] - r[0]) for r, i in zip(out, _INST)]),
        ch=np.array([r[2] for r in out]),
        nd=np.array([r[3] for r in out]))


def _exact_job(k):
    i = _INST[k]
    return k, exact_cvp(i["B"], i["Bs"], i["nrm"], i["t"], i["true"], limit=EXACT_LIMIT)


def lattice_bank(seed, d):
    """V2_LATTICES fresh lattices at dim d; returns (tuning instances, held-out instances)."""
    np.random.seed(seed)
    reduced = gpu_lll([generate_qary_lattice(d, Q) for _ in range(V2_LATTICES)])
    sets = ([], [])
    for k, (B, Bs, nrm) in enumerate(reduced):
        for r in V2_NOISE:
            for _ in range(V2_TARGETS):
                sets[k % 2].append(dict(make_target(B, Bs, nrm, r), lat=k))
    return sets


def cheapest(res, kind, target):
    ok = [c for c in res if c[0] == kind and res[c]["ok"].mean() >= target]
    return min(ok, key=lambda c: res[c]["nd"].sum()) if ok else None


def cluster_boot(a, b, lat, reps=2000):
    """95% intervals for accuracy(a) - accuracy(b) and nodes(a) / nodes(b), resampling whole
    lattices, because targets on one lattice are not independent."""
    ids = np.unique(lat)
    idx = [np.flatnonzero(lat == k) for k in ids]
    okd = np.array([a["ok"][m].sum() - b["ok"][m].sum() for m in idx], float)
    cnt = np.array([len(m) for m in idx], float)
    na = np.array([a["nd"][m].sum() for m in idx], float)
    nb = np.array([b["nd"][m].sum() for m in idx], float)
    rng = np.random.default_rng(0)
    pick = rng.integers(0, len(ids), (reps, len(ids)))
    diff = okd[pick].sum(1) / cnt[pick].sum(1) * 100
    ratio = na[pick].sum(1) / nb[pick].sum(1)
    return [float(x) for x in (*np.percentile(diff, [2.5, 97.5]), *np.percentile(ratio, [2.5, 97.5]))]


def compare(base, va_res, test):
    """base against adaptive VA-ANP on held-out data, overall and per noise level."""
    noise = np.array([i["ratio"] for i in test])
    x, y, p = mcnemar(base["ok"], va_res["ok"])
    lo, hi, rlo, rhi = cluster_boot(base, va_res, np.array([i["lat"] for i in test]))
    out = dict(base_acc=base["ok"].mean() * 100, va_acc=va_res["ok"].mean() * 100,
               ratio=base["nd"].sum() / va_res["nd"].sum(), base_only=x, va_only=y, p=p,
               acc_ci=[lo, hi], ratio_ci=[rlo, rhi], noise={})
    loss = x > y and p < V2_ALPHA
    for r in V2_NOISE:
        m = noise == r
        nx, ny, np_ = mcnemar(base["ok"][m], va_res["ok"][m])
        out["noise"][str(r)] = dict(base_acc=base["ok"][m].mean() * 100, va_acc=va_res["ok"][m].mean() * 100,
                                    ratio=base["nd"][m].sum() / va_res["nd"][m].sum(),
                                    base_only=nx, va_only=ny, p=np_)
        loss = loss or (nx > ny and np_ < V2_ALPHA)
    out["significant_loss"] = bool(loss)
    out["passes_rule"] = bool(out["ratio"] >= V2_RULE_RATIO and not loss)
    return out


def show_compare(label, cfg, c):
    print(f"    vs {label} {cfg}: nodes {c['ratio']:.2f}x (95% CI {c['ratio_ci'][0]:.2f}-{c['ratio_ci'][1]:.2f}), "
          f"accuracy {c['base_acc']:.1f}% vs VA {c['va_acc']:.1f}% "
          f"(diff CI {c['acc_ci'][0]:+.1f} to {c['acc_ci'][1]:+.1f}), "
          f"base-only/VA-only {c['base_only']}/{c['va_only']} p={c['p']:.4f} "
          f"=> {'PASS' if c['passes_rule'] else 'FAIL'}")
    for r, n in c["noise"].items():
        print(f"      noise={r}: {n['base_acc']:.1f}% vs {n['va_acc']:.1f}%, nodes {n['ratio']:.2f}x, "
              f"{n['base_only']}/{n['va_only']} p={n['p']:.4f}")


def speed_check(test):
    """Step 4: the same decoders, original vs vectorized. Must return the same points."""
    sample = test[::6]
    s = lambda i: (i["B"], i["Bs"], i["nrm"], i["t"])
    pairs = {"ANP": (run_anp, lambda i: V.anp(*s(i))),
             "VA-ANP": (run_va, lambda i: V.va(*s(i), i["sigma"], sphere=2.8)),
             "Beam k=2": (run_lp2, lambda i: V.beam(*s(i), k=2))}
    algos = {}
    for name, (old, new) in pairs.items():
        algos[name + " original"], algos[name + " vectorized"] = old, new
    res = evaluate(algos, sample)
    out = {}
    for name in pairs:
        o, n = res[name + " original"], res[name + " vectorized"]
        diff = sum(not np.allclose(a, b, atol=1e-6) for a, b in zip(o["v"], n["v"]))
        assert diff == 0, f"{name}: vectorized differs from the original on {diff} instances"
        out[name] = dict(original_ms=o["t"].mean() * 1000, vectorized_ms=n["t"].mean() * 1000,
                         speedup=o["t"].sum() / n["t"].sum())
        print(f"    {name:<9} original {out[name]['original_ms']:8.3f} ms, vectorized "
              f"{out[name]['vectorized_ms']:8.3f} ms, {out[name]['speedup']:5.2f}x, same points on {len(sample)}",
              flush=True)
    return out


def v2_dim(d, results):
    t0 = time.time()
    print(f"\n=== dim {d} ===", flush=True)
    tune, test = lattice_bank(5000 + d, d)
    print(f"  {len(tune)} tuning and {len(test)} held-out instances from {V2_LATTICES} lattices", flush=True)

    print("  [speed] original vs vectorized", flush=True)
    speed = speed_check(test)

    cfgs = v2_configs()
    with ProcessPoolExecutor(max_workers=16, initializer=_init_worker, initargs=(tune,)) as pool:
        res_tune = dict(pool.map(_cfg_job, cfgs))
    print(f"  tuning sweep of {len(cfgs)} settings done at {time.time() - t0:.0f}s", flush=True)
    exact_idx = list(range(0, len(test), 3))
    with ProcessPoolExecutor(max_workers=16, initializer=_init_worker, initargs=(test,)) as pool:
        res_test = dict(pool.map(_cfg_job, cfgs))
        solved = dict(pool.map(_exact_job, exact_idx, chunksize=4))
    print(f"  held-out sweep and exact CVP done at {time.time() - t0:.0f}s", flush=True)

    # Ceiling: exact on a third of the held-out set; "unknown" hit the search limit.
    known = {k: s for k, s in solved.items() if s is not None}
    for k, s in known.items():  # no decoder may beat the exact solver
        best = min(float(res_test[c]["dist"][k]) for c in cfgs)
        assert norm(test[k]["t"] - s) <= best + 1e-6, "a decoder beat exact CVP"
    # Only a full solve gives a ceiling: the instances over the limit are the hard ones, so a partial mean is too high.
    ceil = np.mean([norm(s - test[k]["true"]) < 1e-3 for k, s in known.items()]) * 100 if len(known) == len(exact_idx) else None
    truth = np.array([norm(i["t"] - i["true"]) for i in test])
    best_found = np.min([res_test[c]["dist"] for c in cfgs], axis=0)
    upper = float(np.mean(best_found >= truth - 1e-6) * 100)
    print(f"  ceiling: exact {ceil if ceil is None else round(float(ceil), 1)}% "
          f"({len(known)} solved, {len(exact_idx) - len(known)} over the search limit); "
          f"at most {upper:.1f}% from decoders alone")
    closest = {}
    for c in cfgs:
        hit = [norm(test[k]["t"] - known[k]) >= res_test[c]["dist"][k] - 1e-6 for k in known]
        closest[str(c)] = float(np.mean(hit) * 100) if hit else None

    row = lambda c: dict(cfg=str(c), kind=c[0], tune_acc=res_tune[c]["ok"].mean() * 100,
                         test_acc=res_test[c]["ok"].mean() * 100,
                         nodes=res_test[c]["nd"].mean(), planes=res_test[c]["ch"].sum() / res_test[c]["nd"].sum(),
                         closest=closest[str(c)])
    out = dict(dim=d, n_test=len(test), ceiling=None if ceil is None else float(ceil), exact_solved=len(known),
               exact_tried=len(exact_idx), ceiling_upper=upper, speed=speed, rows=[row(c) for c in cfgs], margins={})

    print("  Notebook settings on held-out data:")
    for name, c in (("ANP thr=0.35 cap=2n", ("anp", 0.35, 2)), ("VA-ANP llr=2.2 cap=2n", ("va", 2.2, 2))):
        r = row(c)
        print(f"    {name:<24} {r['test_acc']:5.1f}%  {r['nodes']:8.0f} nodes  {r['planes']:.2f} planes/node")

    best_tune = max(res_tune[c]["ok"].mean() for c in cfgs)
    for margin in V2_MARGINS:
        target = best_tune - margin
        picks = {f: cheapest(res_tune, k, target) for f, k in FAMILIES.items()}
        print(f"\n  Target: within {margin * 100:.0f} point(s) of the best tuning accuracy, so {target * 100:.1f}%")
        timed = {f: c for f, c in picks.items() if c}
        tm = evaluate({f: (lambda i, c=c: run_cfg(c, i)) for f, c in timed.items()}, test[::3])
        for f, c in picks.items():
            if c is None:
                print(f"    {f:<18} cannot reach the target")
                continue
            r = row(c)
            print(f"    {f:<18} {str(c):<22} tune {r['tune_acc']:5.1f}%  held-out {r['test_acc']:5.1f}%  "
                  f"{r['nodes']:8.0f} nodes  {tm[f]['t'].mean() * 1000:8.3f} ms", flush=True)
        m = dict(target=target * 100, picks={f: None if c is None else row(c) for f, c in picks.items()},
                 ms={f: tm[f]["t"].mean() * 1000 for f in timed})
        ad = picks["VA-ANP adaptive"]
        if ad is not None:
            base = [f for f in ("ANP fixed list", "Beam fixed list", "LP per-level") if picks[f]]
            m["vs"] = {}
            for f in base:
                m["vs"][f] = compare(res_test[picks[f]], res_test[ad], test)
                show_compare(f, picks[f], m["vs"][f])
            if picks["ANP adaptive"]:
                m["vs_anp_adaptive"] = compare(res_test[picks["ANP adaptive"]], res_test[ad], test)
                show_compare("ANP adaptive", picks["ANP adaptive"], m["vs_anp_adaptive"])
        out["margins"][str(margin)] = m
    results.append(out)
    print(f"  [dim {d} done in {time.time() - t0:.0f}s]", flush=True)


def exp_v2():
    print("Machine:", platform.platform(), "|", platform.processor(), "| numpy", np.__version__, flush=True)
    print(f"Success rule (set before running): at dims 30-40, on held-out data, at least {V2_RULE_RATIO}x fewer "
          f"nodes than the best tuned baseline, with no significant accuracy loss (alpha {V2_ALPHA:.4f}).", flush=True)
    exp0()
    results = []
    for d in V2_DIMS:
        v2_dim(d, results)
        Path(__file__).with_name("v2_results.json").write_text(json.dumps(results, indent=1, default=float))


def exp_v2_noise():
    """Follow-up to exp_v2, not part of its rule. Pooled picks can hide a win at one noise level, and a real
    attack knows its sigma, so every decoder retunes for each noise level. Counts nodes only, so load doesn't matter."""
    caps = (0.25, 0.5, 1, 2, 4, 8)
    cfgs = [("anp", t, x) for t in (0.35, 0.5, 0.7, 0.85) for x in caps]
    cfgs += [("beam", 2, x) for x in (0.125, *caps, 16)]
    cfgs += [("va", l, x) for l in (1.5, 2.2, 3.0, 4.0) for x in caps]
    cfgs += [("va_T", l, T) for l in (2.2, 4.0) for T in TS]
    cfgs += [("beam_T", T) for T in TS]
    fams = {"ANP fixed list": "anp", "Beam fixed list": "beam", "VA-ANP fixed list": "va",
            "VA-ANP adaptive": "va_T", "Beam adaptive": "beam_T"}
    results = []
    for d in (16, 30, 40):
        t0 = time.time()
        print(f"\n=== dim {d} ===", flush=True)
        tune, test = lattice_bank(5000 + d, d)  # same lattices and targets as exp_v2
        with ProcessPoolExecutor(max_workers=16, initializer=_init_worker, initargs=(tune,)) as pool:
            res_tune = dict(pool.map(_cfg_job, cfgs))
        with ProcessPoolExecutor(max_workers=16, initializer=_init_worker, initargs=(test,)) as pool:
            res_test = dict(pool.map(_cfg_job, cfgs))
        print(f"  sweeps done at {time.time() - t0:.0f}s", flush=True)
        for r in V2_NOISE:
            mt = np.array([i["ratio"] == r for i in tune])
            mh = np.array([i["ratio"] == r for i in test])
            rt = {c: {k: v[mt] for k, v in res_tune[c].items()} for c in cfgs}
            rh = {c: {k: v[mh] for k, v in res_test[c].items()} for c in cfgs}
            lat = np.array([i["lat"] for i in test])[mh]
            best = max(v["ok"].mean() for v in rt.values())
            for margin in V2_MARGINS:
                picks = {f: cheapest(rt, k, best - margin) for f, k in fams.items()}
                print(f"  noise={r} target {(best - margin) * 100:.1f}%", flush=True)
                row = dict(dim=d, noise=r, margin=margin, target=(best - margin) * 100, picks={}, vs={})
                for f, c in picks.items():
                    if c is None:
                        print(f"    {f:<18} cannot reach the target")
                        row["picks"][f] = None
                        continue
                    row["picks"][f] = dict(cfg=str(c), tune_acc=rt[c]["ok"].mean() * 100,
                                           test_acc=rh[c]["ok"].mean() * 100, nodes=float(rh[c]["nd"].mean()))
                    print(f"    {f:<18} {str(c):<22} tune {rt[c]['ok'].mean() * 100:5.1f}%  "
                          f"held-out {rh[c]['ok'].mean() * 100:5.1f}%  {rh[c]['nd'].mean():8.0f} nodes", flush=True)
                for v in ("VA-ANP fixed list", "VA-ANP adaptive"):
                    for b in ("ANP fixed list", "Beam fixed list"):
                        if picks[v] and picks[b]:
                            a, o = rh[picks[b]], rh[picks[v]]
                            x, y, p = mcnemar(a["ok"], o["ok"])
                            lo, hi, rlo, rhi = cluster_boot(a, o, lat)
                            ratio = float(a["nd"].sum() / o["nd"].sum())
                            ok = ratio >= V2_RULE_RATIO and not (x > y and p < V2_ALPHA)
                            row["vs"][f"{v} vs {b}"] = dict(ratio=ratio, ratio_ci=[rlo, rhi], acc_ci=[lo, hi],
                                                            base_only=x, va_only=y, p=p, passes=bool(ok))
                            print(f"    {v} vs {b}: nodes {ratio:.2f}x ({rlo:.2f}-{rhi:.2f}), base-only/VA-only "
                                  f"{x}/{y} p={p:.4f} => {'PASS' if ok else 'FAIL'}", flush=True)
                results.append(row)
        Path(__file__).with_name("v2_noise_results.json").write_text(json.dumps(results, indent=1, default=float))
        print(f"  [dim {d} done in {time.time() - t0:.0f}s]", flush=True)


def exp_v2_planes():
    """Dim 40, noise 0.24 is the one case where VA-ANP adaptive beat every baseline. Is that its plane rule,
    or just more list than the grid gave Beam, or a third plane? Same lattices and targets as exp_v2."""
    r, d = 0.24, 40
    tune, test = lattice_bank(5000 + d, d)
    tune, test = [i for i in tune if i["ratio"] == r], [i for i in test if i["ratio"] == r]
    cfgs = [("beam", 2, x) for x in (8, 16, 32, 64)] + [("beam", 3, x) for x in (8, 16, 32, 64)]
    cfgs += [("beam_T", T) for T in (8, 12)] + [("beam3_T", T) for T in (6, 8, 12)]
    cfgs += [("va", 4.0, x) for x in (8, 16, 32, 64)] + [("va_T", 4.0, T) for T in (6, 8, 12)]
    with ProcessPoolExecutor(max_workers=16, initializer=_init_worker, initargs=(tune,)) as pool:
        res_tune = dict(pool.map(_cfg_job, cfgs))
    with ProcessPoolExecutor(max_workers=16, initializer=_init_worker, initargs=(test,)) as pool:
        res_test = dict(pool.map(_cfg_job, cfgs))
    ref = res_test[("va_T", 4.0, 8)]
    rows = []
    for c in cfgs:
        a = res_test[c]
        x, y, p = mcnemar(a["ok"], ref["ok"])
        rows.append(dict(cfg=str(c), tune_acc=res_tune[c]["ok"].mean() * 100, test_acc=a["ok"].mean() * 100,
                         nodes=float(a["nd"].mean()), this_only=x, va_only=y, p=p))
        print(f"  {str(c):<22} tune {rows[-1]['tune_acc']:5.1f}%  held-out {rows[-1]['test_acc']:5.1f}%  "
              f"{rows[-1]['nodes']:8.0f} nodes  vs VA-ANP T=8: this-only/VA-only {x}/{y} p={p:.4f}", flush=True)
    Path(__file__).with_name("v2_planes_results.json").write_text(json.dumps(rows, indent=1, default=float))


if __name__ == "__main__":
    if "--v2" in sys.argv:
        exp_v2()
        raise SystemExit
    if "--v2-planes" in sys.argv:
        exp_v2_planes()
        raise SystemExit
    if "--v2-noise" in sys.argv:
        exp_v2_noise()
        raise SystemExit
    start = time.time()
    # LLL runs on the GPU and exact CVP on a CPU pool; decoder timings stay in this one CPU process.
    POOL = ProcessPoolExecutor(max_workers=16)
    for fn in (exp0, expA, expB, expC, expE, expD):
        fn()
        print(f"  [{fn.__name__} done at {time.time() - start:.0f}s]", flush=True)
    POOL.shutdown()
