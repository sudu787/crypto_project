"""Vectorized BDD decoders, plus VA-ANP with an adaptive candidate list.

All decoders share one loop. The candidate list is one NumPy matrix, so each level costs a few
array operations instead of a Python loop over candidates.

Every decoder returns (point, seconds, children, nodes), the shape stress_test_va_anp.evaluate
expects. nodes = candidates visited, children = candidates created; neither depends on machine load.

Run the self-check: python va_anp_v2.py  (needs stress_test_va_anp.py and the notebook beside it)
"""
import math
import time
from functools import lru_cache

import numpy as np


@lru_cache(maxsize=None)
def _offsets(k):
    """Schnorr-Euchner zig-zag: 0, +1, -1, +2, -2, ... in units of the nearer side."""
    return np.array([0] + [s * o for o in range(1, k) for s in (1, -1)])[:k]


def _decode(B, Bs, nrm, t, planes, rule, sigma=None, T=None, cap=None, ordered=False):
    """Shared decoder loop.

    planes(i): how many planes to consider at level i.
    rule(f, d, acc, nsq): boolean mask of which planes to keep (None = keep all).
    T: if set, drop candidates worse than the best by more than T * 2 sigma^2 (log-likelihood).
    cap: hard limit on the list size, keeping the closest candidates.
    ordered: fully sort when capping, needed only to match the notebook's sphere rule exactly.
    """
    start = time.perf_counter()
    n = B.shape[0]
    R = t.astype(float)[None].copy()
    acc = np.zeros(1)
    nodes = children = 0
    slack = None if T is None else T * 2.0 * sigma ** 2

    for i in range(n - 1, -1, -1):
        nodes += len(acc)
        c = R @ Bs[i] / nrm[i]
        m0 = np.rint(c)  # rounds halves to even, like Python's round()
        f = c - m0
        side = np.where(f >= 0, 1.0, -1.0)
        k = planes(i)
        m = m0[:, None] + side[:, None] * _offsets(k)[None]
        d = (c[:, None] - m) ** 2 * nrm[i]

        keep = rule(f, d, acc, nrm[i]) if rule is not None else None
        if keep is None:
            pi = np.repeat(np.arange(len(acc)), k)
            pj = np.tile(np.arange(k), len(acc))
        else:
            pi, pj = np.nonzero(keep)
        new_acc = acc[pi] + d[pi, pj]
        children += len(new_acc)

        # Choose survivors first, so residuals are only computed for candidates that stay.
        sel = None
        if slack is not None:
            sel = np.flatnonzero(new_acc <= new_acc.min() + slack)
        if cap is not None and (len(new_acc) if sel is None else len(sel)) > cap:
            pool = new_acc if sel is None else new_acc[sel]
            top = np.argsort(pool, kind="stable")[:cap] if ordered else np.argpartition(pool, cap - 1)[:cap]
            sel = top if sel is None else sel[top]
        if sel is not None:
            pi, pj, new_acc = pi[sel], pj[sel], new_acc[sel]

        R = R[pi] - m[pi, pj, None] * B[i]
        acc = new_acc

    return t - R[np.argmin(acc)], time.perf_counter() - start, children, nodes


def babai(B, Bs, nrm, t):
    return _decode(B, Bs, nrm, t, lambda i: 1, None)


def beam(B, Bs, nrm, t, k=2, cap=None, sigma=None, T=None):
    """The notebook's "LP": the same k planes at every level, with a fixed list size."""
    return _decode(B, Bs, nrm, t, lambda i: k, None, sigma=sigma, T=T,
                   cap=2 * B.shape[0] if cap is None else cap)


def anp(B, Bs, nrm, t, thr=0.35, cap=None, sigma=None, T=None):
    """ANP: a second plane only when 2|frac| exceeds a fixed threshold."""
    def rule(f, d, acc, nsq):
        return np.stack([np.ones(len(f), bool), 2.0 * np.abs(f) > thr], 1)
    return _decode(B, Bs, nrm, t, lambda i: 2, rule, sigma=sigma, T=T,
                   cap=2 * B.shape[0] if cap is None else cap)


def va(B, Bs, nrm, t, sigma, llr=2.2, cap=None, T=None, sphere=None):
    """VA-ANP. A further plane is kept only while its log-likelihood loss is under llr.

    sphere is the notebook's sphere_mult. It stays here only so the equivalence check can match
    the original; it changed nothing measurable (1.50 ms with it, 1.49 ms without).
    """
    n = B.shape[0]
    pen = llr * 2.0 * sigma ** 2
    radius = None if sphere is None else sphere * n * sigma ** 2

    def rule(f, d, acc, nsq):
        excess = d - d[:, :1]
        keep = np.empty(d.shape, bool)
        keep[:, 0] = True
        keep[:, 1] = excess[:, 1] <= pen
        keep[:, 2] = keep[:, 1] & (excess[:, 2] <= pen)
        if radius is not None:
            keep &= acc[:, None] + d <= radius
            keep[0, 0] = True  # the first parent's best child always survives, as in the notebook
        return keep

    return _decode(B, Bs, nrm, t, lambda i: 3, rule, sigma=sigma, T=T,
                   cap=2 * n if cap is None else cap, ordered=sphere is not None)


def lp_planes(nrm, sigma, budget):
    """Lindner-Peikert per-level plane counts d_i: raise the level with the lowest success
    probability erf(d_i ||b*_i|| / (2 sqrt(2) sigma)) until the product of d_i reaches budget."""
    d = np.ones(len(nrm), int)
    g = np.sqrt(nrm) / (2.0 * math.sqrt(2.0) * sigma)
    leaves = 1
    while True:
        i = int(np.argmin([math.erf(x) for x in d * g]))
        if leaves // d[i] * (d[i] + 1) > budget:
            return d
        leaves = leaves // d[i] * (d[i] + 1)
        d[i] += 1


def lp(B, Bs, nrm, t, d):
    """Lindner-Peikert NearestPlanes: d[i] planes at level i, no list limit."""
    return _decode(B, Bs, nrm, t, lambda i: int(d[i]), None)


def _self_check(count=1200):
    """Vectorized decoders must return the same points and counts as the notebook's originals."""
    import stress_test_va_anp as S

    insts = S.bank([900], dims=[10, 12, 14, 16], ratios=[0.18, 0.24, 0.30], trials=count // 12)
    pairs = {
        "babai": (lambda i: babai(i["B"], i["Bs"], i["nrm"], i["t"]),
                  lambda i: S.babai_np(i["B"], i["Bs"], i["nrm"], i["t"]) + (None, None)),
        "beam k=2": (lambda i: beam(i["B"], i["Bs"], i["nrm"], i["t"], k=2),
                     lambda i: S.lp_fixed(i["B"], i["Bs"], i["nrm"], i["t"], num_planes=2) + (None, None)),
        "beam k=3": (lambda i: beam(i["B"], i["Bs"], i["nrm"], i["t"], k=3),
                     lambda i: S.lp_fixed(i["B"], i["Bs"], i["nrm"], i["t"], num_planes=3) + (None, None)),
        "anp": (lambda i: anp(i["B"], i["Bs"], i["nrm"], i["t"]), S.run_anp),
        "va": (lambda i: va(i["B"], i["Bs"], i["nrm"], i["t"], i["sigma"], sphere=2.8), S.run_va),
    }
    for name, (new, old) in pairs.items():
        wrong_point = wrong_count = 0
        for i in insts:
            v1, _, c1, n1 = new(i)
            v0, _, c0, n0 = old(i)
            wrong_point += not np.allclose(v1, v0, atol=1e-6)
            wrong_count += c0 is not None and (c0, n0) != (c1, n1)
        print(f"  {name:<9} {len(insts)} instances: different point {wrong_point}, different counts {wrong_count}",
              flush=True)
        assert wrong_point == 0 and wrong_count == 0, f"{name} does not match the original"

    # Pruning off and cap at 2n must give the same result as plain VA-ANP without the sphere check.
    for i in insts[:300]:
        a = va(i["B"], i["Bs"], i["nrm"], i["t"], i["sigma"])
        b = va(i["B"], i["Bs"], i["nrm"], i["t"], i["sigma"], T=1e18)
        assert np.array_equal(a[0], b[0]) and a[2:] == b[2:], "T=infinity changed the result"

    # With a large budget, per-level planes must return the closest point at low noise.
    low = S.bank([901], dims=[12], ratios=[0.10], trials=30)
    ok = sum(np.linalg.norm(lp(i["B"], i["Bs"], i["nrm"], i["t"], lp_planes(i["nrm"], i["sigma"], 64))[0] - i["true"]) < 1e-3
             for i in low)
    assert ok == len(low), "per-level LP missed easy instances"
    print("  all checks passed", flush=True)


if __name__ == "__main__":
    _self_check()
