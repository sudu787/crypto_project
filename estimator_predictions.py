"""Lattice-estimator predictions of Babai's success for the lattices in decoding_study.py.

For each setting it asks the estimator itself, PrimalHybrid.beta_params(beta, params, zeta=0, babai=True,
m=n, d=2n), which simulates the reduced profile of our lattice (n q-vectors, n unit vectors, dimension 2n)
and applies prob.babai with norm sqrt(d) * stddev. It also reports the same formula on other shape models
(ZGSA, CN11) and on our real reduced profiles, to separate profile error from formula error.

Run in WSL under Sage, after decoding_study.py --profiles:
  ~/bin/micromamba run -n sage python estimator_predictions.py "/mnt/d/ABHILASH CRYPTO PROJECT"
"""
import json
import os
import subprocess
import sys

ROOT = sys.argv[1]
EST = os.path.expanduser("~/lattice-estimator")
sys.path.insert(0, EST)

from sage.all import log, sqrt  # noqa: E402

from estimator import LWE, ND  # noqa: E402
from estimator.lwe_primal import PrimalHybrid  # noqa: E402
from estimator.prob import babai as prob_babai  # noqa: E402
from estimator.simulator import CN11, GSA, ZGSA  # noqa: E402

COMBOS = [(2, 70), (2, 80), (10, 70), (10, 80), (10, 100), (20, 70), (20, 80), (20, 90), (20, 100)]
ETAS = (2, 3)
Q = 3329

profiles = json.load(open(os.path.join(ROOT, "decoding_study_profiles.json")))
commit = subprocess.run(["git", "-C", EST, "log", "-1", "--format=%H %cd"], capture_output=True, text=True).stdout.strip()
out = {"estimator_commit": commit, "settings": {}}
for beta, n in COMBOS:
    d = 2 * n
    shapes = {}
    for name, sim in (("GSA", GSA), ("ZGSA", ZGSA), ("CN11", CN11)):
        try:
            shapes[name] = [float(x) for x in sim(d, n, Q, beta, xi=1, tau=False, dual=True)]
        except Exception as exc:  # keep the others if one shape model fails at small beta
            shapes[name] = repr(exc)
    for eta in ETAS:
        X = ND.CenteredBinomial(eta)
        params = LWE.Parameters(n=n, q=Q, Xs=X, Xe=X, m=n)
        bp = PrimalHybrid.beta_params(beta, params, zeta=0, babai=True, m=n, d=d)
        norm = sqrt(d) * X.stddev
        row = {"beta_params_d": int(bp["d"]), "beta_params_babai": float(bp["babai_probability"]),
               "stddev": float(X.stddev)}
        for name, r in shapes.items():
            row[name] = float(prob_babai(r, norm)) if isinstance(r, list) else r
        row["real"] = [float(prob_babai(profiles[f"{beta},{n},{i}"], norm)) for i in range(16)]
        out["settings"][f"{beta},{n},{eta}"] = row
        print(beta, n, eta, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items() if k != "real"},
              "real mean", round(sum(row["real"]) / 16, 4), flush=True)
    out["settings"][f"{beta},{n}"] = {"log_r": {k: ([float(log(x)) for x in v] if isinstance(v, list) else v)
                                                for k, v in shapes.items()}}
json.dump(out, open(os.path.join(ROOT, "estimator_predictions.json"), "w"))
print("wrote estimator_predictions.json", flush=True)
