"""GPU version of the shared decoder loop in va_anp_v2.py, batching every target on a lattice.

It exists to run experiments faster and must return the same points and counts as the CPU code.
Nodes are the comparison, and they don't depend on hardware. CPU timings remain the speed claim.

Self-check, which needs cached bases from toy_lwe_test.py:
  uv run --no-project --python 3.12 --with numpy --with "torch==2.6.0+cu126"
    --index https://download.pytorch.org/whl/cu126 --index-strategy unsafe-best-match
    python toy_lwe_gpu.py
"""
import time

import numpy as np
import torch

import va_anp_v2 as V

DEV = torch.device("cuda")
F64 = torch.float64
# Candidates x dimension in one batch: about 1.6 GB peak. Past the card's 6 GB, Windows spills to system
# RAM and the largest lists ran 7x slower (132 s against 19 s for LP 65536 on 25 targets at d = 180).
CELLS = 7e7


def _by_target(owner, acc):
    """Candidate indices sorted by target, then by accumulated distance."""
    order = torch.argsort(acc, stable=True)
    return order[torch.argsort(owner[order], stable=True)]


def _decode(B, Bs, nrm, ts, planes, rule, sigma, T, cap, keep_all=False):
    N, d = ts.shape
    R = ts.clone()
    acc = torch.zeros(N, dtype=F64, device=DEV)
    owner = torch.arange(N, device=DEV)
    nodes = torch.zeros(N, dtype=torch.int64, device=DEV)
    children = torch.zeros(N, dtype=torch.int64, device=DEV)
    slack = None if T is None else T * 2.0 * sigma ** 2
    offsets = {}

    for i in range(d - 1, -1, -1):
        nodes += torch.bincount(owner, minlength=N)
        c = R @ Bs[i] / nrm[i]
        m0 = torch.round(c)  # rounds halves to even, like np.rint
        f = c - m0
        side = 2.0 * (f >= 0).to(F64) - 1.0
        k = planes(i)
        if k not in offsets:
            offsets[k] = torch.as_tensor(V._offsets(k), dtype=F64, device=DEV)
        m = m0[:, None] + side[:, None] * offsets[k][None]
        dist = (c[:, None] - m) ** 2 * nrm[i]

        if rule is None:
            pi = torch.arange(len(acc), device=DEV).repeat_interleave(k)
            pj = torch.arange(k, device=DEV).repeat(len(acc))
        else:
            pi, pj = torch.nonzero(rule(f, dist), as_tuple=True)
        new_acc = acc[pi] + dist[pi, pj]
        new_owner = owner[pi]
        children += torch.bincount(new_owner, minlength=N)

        if slack is not None:
            best = torch.full((N,), torch.inf, dtype=F64, device=DEV).scatter_reduce(0, new_owner, new_acc, "amin")
            sel = torch.nonzero(new_acc <= best[new_owner] + slack).squeeze(1)
            pi, pj, new_acc, new_owner = pi[sel], pj[sel], new_acc[sel], new_owner[sel]
        if cap is not None:
            counts = torch.bincount(new_owner, minlength=N)
            if counts.max() > cap:
                order = _by_target(new_owner, new_acc)
                start = torch.cumsum(counts, 0) - counts
                sel = order[torch.arange(len(order), device=DEV) - start[new_owner[order]] < cap]
                pi, pj, new_acc, new_owner = pi[sel], pj[sel], new_acc[sel], new_owner[sel]

        R = R[pi]
        R.addr_(m[pi, pj], B[i], alpha=-1.0)  # in place: one copy of the list fewer at peak; integers, so exact
        acc, owner = new_acc, new_owner

    if keep_all:  # every survivor: R is t minus a lattice point, acc its squared length
        return (R.cpu().numpy(), acc.cpu().numpy(), owner.cpu().numpy()), children.cpu().numpy(), nodes.cpu().numpy()
    counts = torch.bincount(owner, minlength=N)
    first = _by_target(owner, acc)[torch.cumsum(counts, 0) - counts]
    return (ts - R[first]).cpu().numpy(), children.cpu().numpy(), nodes.cpu().numpy()


def decode_all(cfg, B, Bs, nrm, ts, sigma, keep_all=False):
    """All targets for one configuration. Returns (point, seconds, children, nodes) per target.
    With keep_all, the first item is instead (R, acc): every final candidate's t - point as int64,
    in list order, and its squared length; the default pick is R[argmin(acc)]."""
    d = B.shape[0]
    kind = cfg[0]
    planes, rule, T, cap, per_target = (lambda i: 1), None, None, None, 1
    if kind in ("beam", "beam_T"):
        planes = lambda i, k=cfg[1]: k
        T = cfg[2] if kind == "beam_T" else None
        cap = cfg[-1] * d
    elif kind == "anp":
        thr = cfg[1]
        planes = lambda i: 2
        rule = lambda f, dist: torch.stack([torch.ones_like(f, dtype=torch.bool), 2.0 * f.abs() > thr], 1)
        cap = cfg[2] * d
    elif kind in ("va", "va_T"):
        pen = cfg[1] * 2.0 * sigma ** 2
        T = cfg[2] if kind == "va_T" else None
        cap = cfg[-1] * d
        planes = lambda i: 3

        def rule(f, dist):
            ex = dist - dist[:, :1]
            second = ex[:, 1] <= pen
            return torch.stack([torch.ones_like(second), second, second & (ex[:, 2] <= pen)], 1)
    elif kind == "lp":
        counts = V.lp_planes(nrm, sigma, cfg[1])
        planes = lambda i: int(counts[i])
        per_target = cfg[1]
    elif kind != "babai":
        raise ValueError(cfg)
    if cap is not None:
        per_target = cap

    to = lambda x: torch.as_tensor(np.asarray(x, dtype=float), dtype=F64, device=DEV)
    Bg, Bsg, nrmg = to(B), to(Bs), to(nrm)
    size = max(1, int(CELLS / d / per_target))
    out = []
    for at in range(0, len(ts), size):
        chunk = ts[at:at + size]
        start = time.perf_counter()
        points, children, nodes = _decode(Bg, Bsg, nrmg, to(chunk), planes, rule, sigma, T, cap, keep_all)
        secs = (time.perf_counter() - start) / len(chunk)
        if keep_all:
            R, acc, owner = points
            points = [(np.rint(R[owner == j]).astype(np.int64), acc[owner == j]) for j in range(len(chunk))]
        out += [(p, secs, int(c), int(n)) for p, c, n in zip(points, children, nodes)]
    return out


def _self_check():
    """Same points and counts as the CPU code, across every decoder kind and both list rules."""
    import toy_lwe_test as T

    cfgs = T.ALL_CFGS[::4] + [("babai",), ("beam", 3, 8), ("va_T", 4.0, 16.0, 64), ("lp", 1024)]
    checked = 0
    for n, beta, idx in ((70, 2, 0), (90, 10, 1)):
        A = T.make_A(T.TAGS["pilot"], n, n, idx)
        B, _ = T.reduced(T.TAGS["pilot"], n, n, beta, idx, 0)
        assert all(T.is_lattice_point(row.astype(float), A) for row in B), "A doesn't match the cached basis"
        Bs, nrm = T.gso(B)
        tg = T.make_targets(A, T.TAGS["pilot"], 2, idx, 4)
        ts = np.stack([np.concatenate([np.zeros(n, dtype=np.int64), b]) for *_, b in tg])
        for c in cfgs:
            gpu = decode_all(c, B, Bs, nrm, ts, 1.0)
            for t, (point, _, children, nodes) in zip(ts, gpu):
                ref = T.run_cfg(c, B, Bs, nrm, t, 1.0, {})
                assert np.allclose(point, ref[0], atol=1e-6), f"{c}: different point"
                assert (children, nodes) == (ref[2], ref[3]), f"{c}: counts {children, nodes} vs {ref[2], ref[3]}"
                checked += 1
            print(f"  n={n} {T.beta_name(beta)} {str(c):<28} same points and counts", flush=True)
    print(f"  all {checked} decodes match the CPU code", flush=True)


if __name__ == "__main__":
    _self_check()
