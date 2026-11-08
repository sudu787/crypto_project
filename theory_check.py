"""Numerical checks of the propositions in Retry_theory.md, on real reduced bases (CPU, numpy).

P1  F_B(r) <= Pi_B(r): exact fixed-norm success <= the per-level product (the estimator's prob.babai at radius sqrt r).
P2  E_{r ~ sigma^2 chi2_d} F_B(r) = prod_i erf(c_i / (sigma sqrt 2)) (Gaussian error), and how close the estimator's
    Pi_B(d sigma^2) is to it.
P3  Uses retry_cost_*.npz (per-instance F from the R8 bases): E prod(1-F) >= prod(1-E F); hazard non-increasing;
    restarting after each failure minimises attempts per solved instance.
Monte Carlo: M directions per basis; a P1 violation counts only if F exceeds Pi by more than 4 standard errors.
"""
import glob
import math
import pathlib
import sys

import numpy as np
from scipy.special import betainc, erf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import retry_study as R  # noqa: E402
import toy_lwe_test as T  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
BASES = [("BKZ-20 n=95", "t7_b20_n95_i0_j0.npy", 2), ("BKZ-10 n=85", "t7_b10_n85_i0_j0.npy", 2),
         ("LLL n=78", "t8_b2_n78_i0_j0.npy", 2), ("BKZ-20 n=100", "b20_n100_i0_j0.npy", 2)]
M = 400_000
rng = np.random.default_rng(2026)


def rho_samples(nrm):
    """rho(z) = min_i c_i/|z_i| for z uniform on the sphere: success at radius sqrt(r) iff sqrt(r) < rho."""
    c = np.sqrt(nrm) / 2
    out = []
    for _ in range(M // 20_000):
        z = rng.standard_normal((20_000, len(nrm)))
        z /= np.linalg.norm(z, axis=1, keepdims=True)
        out.append((c / np.abs(z)).min(1))
    return np.sort(np.concatenate(out))


def F(rho, r):
    return 1 - np.searchsorted(rho, np.sqrt(r)) / len(rho)


def Pi(nrm, r):
    d = len(nrm)
    x = np.minimum(1.0, nrm[None, :] / (4 * np.asarray(r, float)[:, None]))
    return np.exp(np.log(np.maximum(betainc(0.5, (d - 1) / 2, x), 1e-300)).sum(1))


print("P1 and P2 on one basis per setting")
allok = True
for name, fn, eta in BASES:
    _, nrm = T.gso(np.load(R.RETRY / fn))
    d, sig2 = len(nrm), eta / 2
    rho = rho_samples(nrm)
    r = d * sig2 * np.linspace(0.6, 1.4, 33)
    f, p = F(rho, r), Pi(nrm, r)
    se = np.sqrt(np.maximum(f * (1 - f), 1 / M) / M)
    viol = int((f > p + 4 * se).sum())
    allok &= viol == 0
    m = p > 1e-4
    ratio = (p[m] / np.maximum(f[m], 1e-12))
    # P2: Gaussian error of variance sig2 per coordinate
    g = float(np.prod(erf(np.sqrt(nrm) / 2 / math.sqrt(2 * sig2))))
    rs = sig2 * rng.chisquare(d, 400_000)
    favg = float(F(rho, rs).mean())
    o = rng.standard_normal((200_000, d)) * math.sqrt(sig2)  # direct check in the GS frame
    direct = float((np.abs(o) < np.sqrt(nrm) / 2).all(1).mean())
    est = float(Pi(nrm, [d * sig2])[0])
    print(f"  {name}: P1 violations {viol}/33; Pi/F on r in [0.6, 1.4] d sigma^2 (where Pi > 1e-4): "
          f"{ratio.min():.3f}-{ratio.max():.3f}")
    print(f"     P2: prod erf {g:.4f} | E_r F(r) {favg:.4f} | direct Gaussian MC {direct:.4f} | estimator Pi(d sigma^2) {est:.4f}")
assert allok, "P1 violated beyond Monte Carlo error"

files = sorted(glob.glob(str(HERE / "retry_cost_t*.npz")))
if not files:
    print("P3: no retry_cost_*.npz yet (run retry_cost.py)")
    sys.exit()
print("P3 on per-instance exact-law probabilities (R8 and exploratory BKZ bases)")
for fpath in files:
    z = np.load(fpath)
    for eta in R.ETAS:
        Fb = z[f"F_{eta}"].mean(2).ravel()
        K = z[f"F_{eta}"].shape[2]
        lhs, rhs = float(np.mean((1 - Fb) ** K)), float((1 - Fb.mean()) ** K)
        D = np.array([np.mean((1 - Fb) ** k) for k in range(200)])
        h = 1 - D[1:] / D[:-1]
        mono = bool(np.all(np.diff(h) <= 1e-12))
        cost = [np.sum(D[:k]) / (1 - D[k]) for k in (1, 2, 4, 16, 64, 199)]
        ok = lhs >= rhs and mono and all(c >= cost[0] - 1e-9 for c in cost)
        allok &= ok
        print(f"  {pathlib.Path(fpath).stem} eta={eta}: P(all {K} fail) {lhs:.4f} >= indep {rhs:.4f}; hazard "
              f"{h[0]:.4f} -> {h[63]:.4f} -> {h[-1]:.4f} non-increasing {mono}; attempts per solved instance, give up "
              f"after 1/2/4/16/64/199: " + "/".join(f"{c:.1f}" for c in cost) + f"  {'OK' if ok else 'FAIL'}")
assert allok
print("all checks passed")
