"""Item 4: why LLL breaks the fixed-norm law (rule R11).

Exploratory findings (geometry of the bases only, no decoding outcomes; scratchpad lll_similar*.py, zshape.py).
Directions are mapped back to the instance's own coordinates; "overlap" is ||U_a U_b^T||_F^2 / 8 for the last 8
Gram-Schmidt directions of two bases (the levels that decide Babai).
  * LLL's last directions sit mostly in the secret block: 69% of their mass at LLL n=78, against 59% (BKZ-10 n=85)
    and 56% (BKZ-20 n=95). So on LLL bases success depends on ||s|| and ||e|| separately, not only on ||o||:
    this is why the norm-only law failed (R6) and the block-aware multiset law did much better (R9).
  * Bases of the SAME lattice are slightly more aligned than bases of different lattices: ratio 1.07 for LLL
    (permutation re-randomisation), 1.04 BKZ-10, 1.00 BKZ-20. An earlier comparison against isotropic random
    subspaces suggested 1.8x; that was mostly the block concentration above, not lattice-specific alignment.
  * No q-vector Z-shape: none of the bases checked has a q-axis row or a Gram-Schmidt norm equal to q.
  * Scrambling (a random unimodular transform before LLL: scramble(), 4d elementary row operations b_i += c b_j,
    c = +-1, as in Gama-Nguyen-Regev extreme pruning) lowers the same/different ratio to 1.05 and the secret-block
    share to 64%; estimator-style success per attempt at n=78: 4.6% (eta=2), 0.45% (eta=3).

R11 (fixed 8 Nov 2026, before any tag-11 basis was reduced). Claim: R9 failed in the tail because permutation-only
    re-randomisation leaves same-lattice LLL bases correlated; with scrambled re-randomisation the block-multiset law
    (retry_study.multiset_probs, no free parameters) accounts for the dependence between attempts.
    Setting: as R9 (LLL n=78, K=128, eta in {2, 3}, 16 lattices x 200 targets, 2,000 permutations per (basis, target)),
    fresh instances (tag 11), each attempt = same coordinate permutation as before, then scramble(), then LLL.
    Same 8 cells and 99% Wilson intervals as R9. Pass: block-multiset model off in at most 1 cell and in fewer cells
    than the independent model, and its predicted count variance within 25% of measured at both eta (degeneracy
    guard as in R8). Reported either way; nothing else is a test.

--probe     WSL: a few scrambled LLL bases of probe lattices (tag 12), timing only.
--overlap   CPU: subspace overlap of scrambled bases (geometry only, no decoding outcome), and their success level
            from the exact law at the expected norm, to fix the R11 setting.
--reduce    WSL: R11 bases (tag 11).
--test      GPU: rule R11 (written below before any tag-11 basis is reduced).
"""
import argparse
import json
import os
import pathlib
import sys
import time

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import retry_study as R  # noqa: E402
import toy_lwe_test as T  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TAG, TEST_TAG = 12, 11


def scramble(B, rng):
    """Random unimodular transform of the rows: 4d elementary operations b_i += c b_j."""
    B = B.copy()
    d = len(B)
    for _ in range(4 * d):
        i, j = rng.choice(d, 2, replace=False)
        B[i] += rng.choice((-1, 1)) * B[j]
    return B


def reduce_scrambled(tag, n, idx, j):
    from fpylll import LLL, IntegerMatrix
    R.TAG = tag
    Pp, Qp = R.perms(n, idx, j)
    B0 = T.q_basis(T.make_A(tag, n, n, idx)[Qp][:, Pp])
    B1 = scramble(B0, np.random.default_rng([tag, n, idx, j, 99]))
    M = IntegerMatrix.from_matrix(B1.tolist())
    t = time.perf_counter()
    LLL.reduction(M)
    d = len(B0)
    return np.array([[M[a, b] for b in range(d)] for a in range(d)], dtype=np.int64), time.perf_counter() - t


def path_for(tag, n, idx, j):
    return R.RETRY / f"u{tag}_n{n}_i{idx}_j{j}.npy"


def _job(job):
    tag, n, idx, j = job
    p = path_for(tag, n, idx, j)
    if not p.exists():
        B, secs = reduce_scrambled(tag, n, idx, j)
        tmp = p.with_name(p.stem + f".{os.getpid()}.tmp.npy")
        np.save(tmp, B)
        tmp.replace(p)
    return job


def reduce_jobs(jobs, workers):
    from concurrent.futures import ProcessPoolExecutor, as_completed
    R.RETRY.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    with ProcessPoolExecutor(workers) as pool:
        for k, f in enumerate(as_completed([pool.submit(_job, jb) for jb in jobs]), 1):
            f.result()
            if k % 64 == 0 or k == len(jobs):
                print(f"  [{k}/{len(jobs)}] {time.perf_counter() - t0:6.0f}s", flush=True)


def to_original(B, n, idx, j, tag):
    """Columns back to the instance's own coordinate order."""
    R.TAG = tag
    Pp, Qp = R.perms(n, idx, j)
    Bo = np.zeros_like(B)
    Bo[:, np.concatenate([Pp, n + Qp])] = B
    return Bo


def overlap(n, tag, lattices, K, loader):
    rows = []
    for idx in range(lattices):
        U = []
        for j in range(K):
            Bs, nrm = T.gso(to_original(loader(idx, j), n, idx, j, tag).astype(float))
            U.append(Bs[-8:] / np.sqrt(nrm[-8:])[:, None])
        ov = [np.linalg.norm(U[a] @ U[b].T) ** 2 / 8 for a in range(K) for b in range(a + 1, K)]
        rows.append(float(np.mean(ov)))
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--overlap", action="store_true")
    ap.add_argument("--n", type=int, default=78)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--reduce", action="store_true")
    a = ap.parse_args()
    if a.reduce:  # R11 bases: LLL n=78, 16 lattices x 128 attempts, tag 11
        reduce_jobs([(TEST_TAG, 78, i, j) for i in range(16) for j in range(128)], a.workers)
    if a.probe:
        reduce_jobs([(PROBE_TAG, a.n, i, j) for i in range(2) for j in range(24)], a.workers)
    if a.overlap:
        n = a.n
        ov = overlap(n, PROBE_TAG, 2, 24, lambda i, j: np.load(path_for(PROBE_TAG, n, i, j)))
        print(f"scrambled LLL n={n}: last-8 GS overlap per lattice {['%.3f' % x for x in ov]}, random level {8 / (2 * n):.3f}")
        _, nrm = T.gso(np.load(path_for(PROBE_TAG, n, 0, 0)))
        from scipy.special import betainc  # noqa: F401
        for eta in (1, 2, 3):
            print(f"  eta={eta}: estimator-style p at sqrt(d sigma^2) {R.p_sphere(nrm, [2 * n * eta / 2])[0]:.4f}")
        delta = (np.sqrt(nrm[0]) / np.exp(np.log(nrm).sum() / (4 * n))) ** (1 / (2 * n))
        print(f"  root-Hermite delta {delta:.5f}; first/last GS norm {np.sqrt(nrm[0]):.1f} / {np.sqrt(nrm[-1]):.2f}")
