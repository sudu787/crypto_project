"""Is the steep real profile just under-converged BKZ? Continue BKZ-beta one tour at a time on cached
held-out bases and print the fitted root-Hermite factor (middle 60% slope) after each tour."""
import sys

import numpy as np
from fpylll import BKZ, GSO, IntegerMatrix

CACHE = "/mnt/c/Users/sudu/toy_lwe_cache"


def delta(M):
    G = GSO.Mat(M, float_type="ld")
    G.update_gso()
    y = 0.5 * np.log([G.get_r(i, i) for i in range(M.nrows)])
    d = len(y)
    x = np.arange(d)
    return float(np.exp(-np.polyfit(x[d // 5:4 * d // 5], y[d // 5:4 * d // 5], 1)[0] / 2))


for spec in sys.argv[1:]:
    beta, n, idx = map(int, spec.split(","))
    B = np.load(f"{CACHE}/t4_n{n}_m{n}_b{beta}_i{idx}.npz")["B"]
    M = IntegerMatrix.from_matrix(B.tolist())
    print(f"BKZ-{beta} n={n} lattice {idx}: cached delta {delta(M):.5f}", flush=True)
    for tour in range(1, 201):
        before = [list(M[i]) for i in range(3)]
        BKZ.reduction(M, BKZ.Param(block_size=beta, flags=BKZ.MAX_LOOPS, max_loops=1), float_type="ld")
        if tour in (1, 2, 4, 8, 16, 32, 64, 100, 150, 200):
            print(f"  +{tour:3d} tours  delta {delta(M):.5f}", flush=True)
