"""Impact of the fixed error on the lattice estimator's hybrid estimate (run in WSL under Sage).

For each parameter set: the estimator's primal_usvp, primal_bdd and primal_hybrid (babai=True, mitm=False).
At the hybrid's optimum it charges amplify(0.99, h * p) repetitions, p = prob_babai(r, sqrt(d) * sigma) on its
simulated profile r, h the guessing hit probability. With the error fixed per instance, ||o||^2 ~ sigma^2 chi^2_d
(the estimator's own Gaussian error model) and the repetitions needed are the k with
E_r[(1 - h p(r))^k] = 0.01. Everything else (beta, d, zeta, profile, h) is the estimator's.
Exploratory: the estimator's model, not measured at these sizes.
"""
import math
import os
import sys

import numpy as np
from scipy.stats import chi2

sys.path.insert(0, os.path.expanduser("~/lattice-estimator"))
from estimator import LWE, schemes  # noqa: E402
from estimator.conf import red_shape_model as red_shape_model_default  # noqa: E402
from estimator.lwe_primal import PrimalUSVP  # noqa: E402
from estimator.prob import babai as prob_babai  # noqa: E402
from estimator.simulator import normalize as simulator_normalize  # noqa: E402

NAMES = sys.argv[1:] or ["TFHE630", "Concrete_TFHE586", "HElib80_1024", "CHHS_1024_25", "SEAL20_1024", "HESv111024128ternary"]
QUANT = (np.arange(400) + 0.5) / 400  # quantiles of chi^2_d


def log2(x):
    return float(math.log2(x)) if x and x > 0 else float("inf")


for name in NAMES:
    params = getattr(schemes, name)
    usvp = LWE.primal_usvp(params)
    bdd = LWE.primal_bdd(params)
    hyb = LWE.primal_hybrid(params, babai=True, mitm=False)
    line = (f"{name}: usvp 2^{log2(usvp['rop']):.1f}  bdd 2^{log2(bdd['rop']):.1f}  "
            f"hybrid(babai) 2^{log2(hyb['rop']):.1f} beta={hyb.get('beta')} d={hyb.get('d')} zeta={hyb.get('zeta')}")
    if "prob" not in hyb or not hyb["prob"]:
        print(line, "(no repetition)", flush=True)
        continue
    beta, d, zeta = int(hyb["beta"]), int(hyb["d"]), int(hyb["zeta"])
    xi = PrimalUSVP._xi_factor(params.Xs, params.Xe)
    r = simulator_normalize(red_shape_model_default)(d, params.n - zeta, params.q, beta, xi=xi, tau=False, dual=True)
    sigma = float(params.Xe.stddev)
    p0 = float(prob_babai(r, math.sqrt(d) * sigma))
    h = float(hyb["prob"]) / p0
    k_est = float(hyb["repetitions"])
    radii2 = sigma ** 2 * chi2.ppf(QUANT, d)
    pr = np.array([float(prob_babai(r, math.sqrt(x))) for x in radii2])
    q = h * pr

    def fail(k):  # E_r[(1 - h p(r))^k], in logs
        return float(np.mean(np.exp(k * np.log1p(-np.minimum(q, 1 - 1e-16)))))

    lo, hi = 1.0, max(2.0, k_est)
    while fail(hi) > 0.01:
        hi *= 2
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if fail(mid) > 0.01 else (lo, mid)
    print(line + f"\n    babai p at sqrt(d)sigma {p0:.3g}, hit h {h:.3g}; repetitions estimator 2^{log2(k_est):.1f}, "
          f"fixed error 2^{log2(hi):.1f} (x{hi / k_est:.2f}); hybrid cost becomes 2^{log2(float(hyb['rop']) * hi / k_est):.1f}",
          flush=True)
