"""Item 5: the lattice estimator with a fixed-error repetition model (run in WSL under Sage, on the local branch
fixed-error-repetitions of ~/lattice-estimator; the patch is estimator_fixed_error.patch in this folder).

For each parameter set: primal_usvp, primal_bdd and primal_hybrid (Babai, with and without MitM) under the
estimator's own repetition model and under repetition_model="fixed_error", where each repetition re-randomises the
basis but attacks the same instance (prob.amplify_fixed_error). Whatever the optimizer picks (beta, zeta, d) is
re-optimised under each model. Exploratory: estimator models, not measured at these sizes.
"""
import math
import os
import sys

sys.path.insert(0, os.path.expanduser("~/lattice-estimator"))
from estimator import LWE, schemes  # noqa: E402

NAMES = sys.argv[1:] or ["TFHE630", "Concrete_TFHE586", "TFHE1024", "HElib80_1024", "HElib120_1024", "CHHS_1024_25",
                         "SEAL20_1024", "HESv111024128ternary", "Kyber512"]


def lg(c):
    x = c["rop"]
    return float(math.log2(x)) if x and x != float("inf") else float("inf")


def show(tag, c):
    keys = ("beta", "zeta", "d", "prob", "repetitions")
    return f"{tag} 2^{lg(c):.1f} (" + ", ".join(f"{k}={c[k]}" if k != "prob" else f"prob={float(c[k]):.3g}"
                                                for k in keys if k in c) + ")"


for name in NAMES:
    params = getattr(schemes, name, None)
    if params is None:
        print(f"{name}: not in estimator.schemes")
        continue
    usvp, bdd = LWE.primal_usvp(params), LWE.primal_bdd(params)
    print(f"{name}: usvp 2^{lg(usvp):.1f}, bdd 2^{lg(bdd):.1f}", flush=True)
    for mitm in (False, True):
        ind = LWE.primal_hybrid(params, babai=True, mitm=mitm)
        fix = LWE.primal_hybrid(params, babai=True, mitm=mitm, repetition_model="fixed_error")
        best_ind = min(lg(usvp), lg(bdd), lg(ind))
        best_fix = min(lg(usvp), lg(bdd), lg(fix))
        print(f"  hybrid babai mitm={mitm}: {show('independent', ind)}\n"
              f"                          {show('fixed error', fix)}\n"
              f"      hybrid +{lg(fix) - lg(ind):.2f} bits; best primal estimate {best_ind:.1f} -> {best_fix:.1f}", flush=True)
