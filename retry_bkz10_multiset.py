"""Does the block-multiset law remove the residual dependence found by retry_calibration.py at BKZ-10 n=85?

Post hoc (exploratory). Same R8 bases (tag 7) and instances as retry_cost_t7_b10_n85.npz. For each instance and
basis: retry_study.multiset_probs, the share of 2,000 within-block permutations of the instance's own offset that
pass every Babai level. Then the per-instance PIT test of retry_calibration.py, with lattice-level bootstrap.
"""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import retry_calibration as C  # noqa: E402
import retry_exact as X  # noqa: E402
import retry_study as R  # noqa: E402
import toy_lwe_test as T  # noqa: E402

TAG, BETA, N, K = 7, 10, 85, 64
OUT = pathlib.Path(__file__).resolve().parent / "retry_cost_t7_b10_n85_multiset.npz"


def compute():
    R.TAG = TAG
    M = {eta: np.zeros((R.LATTICES, R.TARGETS, K)) for eta in R.ETAS}
    for idx in range(R.LATTICES):
        offs = {eta: R.instance_offsets(N, idx, eta) for eta in R.ETAS}
        for j in range(K):
            Bs, nrm = T.gso(np.load(X.heldout_path(BETA, N, idx, j, TAG)))
            Pp, Qp = R.perms(N, idx, j)
            for eta in R.ETAS:
                s, e, _ = offs[eta]
                o = np.concatenate([-s[:, Pp], e[:, Qp]], 1)
                M[eta][idx, :, j] = R.multiset_probs(Bs, nrm, N, o, 2000, seed=(idx * 1000 + j) * 10 + eta)
        print(f"  lattice {idx} done", flush=True)
    np.savez(OUT, **{f"M_{eta}": M[eta] for eta in R.ETAS})


def analyse():
    d, m = np.load("retry_cost_t7_b10_n85.npz"), np.load(OUT)
    rng = np.random.default_rng(2)
    for eta in (2, 3):
        S, F, Mp = d[f"S_{eta}"], d[f"F_{eta}"], m[f"M_{eta}"]
        c = S.sum(-1)
        assert np.all(Mp[S] > 0), "a measured success has multiset probability 0"  # the true order is one of the perms
        print(f"BKZ-10 n=85 eta={eta}: per attempt measured {S.mean():.4f}, exact {F.mean():.4f}, multiset {Mp.mean():.4f}")
        for name, P in (("exact", F), ("multiset", Mp)):
            u = C.pit(P, c, rng)
            ci = C.boot(lambda ix: u[ix].var(), S.shape[0], rng)
            print(f"    {name:8s} PIT var {u.var():.4f} CI {np.round(ci, 4)}  {'ok' if ci[0] <= 1 / 12 <= ci[1] else 'OFF'}")


if __name__ == "__main__":
    if "--analyse" not in sys.argv:
        compute()
    analyse()
