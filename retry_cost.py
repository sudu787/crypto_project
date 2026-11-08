"""Item 2: what the retry dependence costs an attacker, and when to stop retrying one instance.

Data: the R8 bases (tag 7: BKZ-20 n=95, BKZ-10 n=85, K=64) and the exploratory BKZ-20 n=100 bases (tag 4, K=64);
16 lattices x 200 targets, eta in {2, 3}. These are exploratory analyses of data whose test (R8) is already
reported; nothing here is a new pre-registered test.

1. Attempts for 99% success. amplify(0.99, p) = log(0.01)/log(1-p) with p the mean per-attempt success (what the
   estimator does), against the attempts the exact fixed-norm model needs: smallest K with
   mean_t prod_{j<K} (1 - F(r_t)) <= 0.01 (bases cycled, F_t = mean over the instance's bases). Measured share solved
   within k attempts is shown up to k = 64 as a check of the model in range.
2. Hazard: P(success at attempt k+1 | first k failed), measured (averaged over all orderings of each target's
   attempts, via the hypergeometric formula), exact model, independent model (flat).
3. Give-up rule: if the attacker can refresh the instance after k failures (e.g. a fresh subset of LWE samples, which
   gives a fresh e), expected attempts per solved instance = E[sum_{i<k}(1-F)^i] / E[1-(1-F)^k], with the
   expectation over instances. Computed from the exact model and, for k <= 64, from the measured counts.
"""
import json
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import retry_exact as X  # noqa: E402
import retry_study as R  # noqa: E402
import toy_lwe_test as T  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
SETS = [(7, 20, 95, 64), (7, 10, 85, 64), (4, 20, 100, 64)]


def collect(tag, beta, n, K):
    import torch
    import toy_lwe_gpu as G
    R.TAG = tag
    d = 2 * n
    out = {eta: {"S": np.zeros((R.LATTICES, R.TARGETS, K), bool), "F": np.zeros((R.LATTICES, R.TARGETS, K)),
                 "pind": np.zeros((R.LATTICES, K)), "r": np.zeros((R.LATTICES, R.TARGETS))} for eta in R.ETAS}
    for idx in range(R.LATTICES):
        offs = {eta: R.instance_offsets(n, idx, eta) for eta in R.ETAS}
        for j in range(K):
            B = np.load(R.base_path(beta, n, idx, j) if tag == 4 else X.heldout_path(beta, n, idx, j, tag))
            Bs, nrm = T.gso(B)
            U = torch.as_tensor(Bs / np.sqrt(nrm)[:, None], dtype=G.F64, device=G.DEV)
            half = torch.as_tensor(np.sqrt(nrm) / 2, dtype=G.F64, device=G.DEV)
            Pp, Qp = R.perms(n, idx, j)
            os_ = {eta: np.concatenate([-offs[eta][0][:, Pp], offs[eta][1][:, Qp]], 1) for eta in R.ETAS}
            radii = np.concatenate([(os_[eta] ** 2).sum(1) for eta in R.ETAS])
            F = R.exact_curve(nrm, radii, X.M_DIRS, seed=(tag * 1000 + idx) * 1000 + j)
            for k, eta in enumerate(R.ETAS):
                o = torch.as_tensor(os_[eta], dtype=G.F64, device=G.DEV)
                out[eta]["S"][idx, :, j] = ((o @ U.T).abs() < half).all(1).cpu().numpy()
                out[eta]["F"][idx, :, j] = F[k * R.TARGETS:(k + 1) * R.TARGETS]
                out[eta]["pind"][idx, j] = R.p_sphere(nrm, [d * eta / 2])[0]
                out[eta]["r"][idx] = radii[k * R.TARGETS:(k + 1) * R.TARGETS]
        print(f"  tag {tag} {T.beta_name(beta)} n={n} lattice {idx} done", flush=True)
    return out


def fail_prob(counts, K, k):
    """P(first k attempts all fail | c successes among K exchangeable attempts) = C(K-c, k) / C(K, k)."""
    c = np.asarray(counts)
    if k > K:
        return np.full(c.shape, np.nan)
    return np.array([math.comb(K - x, k) / math.comb(K, k) for x in c.ravel()]).reshape(c.shape)


def analyse(data, K):
    res = {}
    for eta, D in data.items():
        S, F, pind = D["S"], D["F"], D["pind"]
        Fbar = F.mean(2).ravel()  # per instance, averaged over its bases
        counts = S.sum(2).ravel()
        pbar_meas, pbar_ind = float(S.mean()), float(pind.mean())
        amp = lambda p: math.log(0.01) / math.log(1 - p) if 0 < p < 1 else float("inf")
        # model attempts for 99% (Fbar per instance; instances with Fbar = 0 never reach it)
        never_model = float((Fbar <= 1e-12).mean())
        k_model = None
        if never_model < 0.01:
            surv = lambda k: float(np.mean((1 - Fbar) ** k))
            lo, hi = 1, 1
            while surv(hi) > 0.01 and hi < 10**9:
                hi *= 2
            while lo < hi:
                mid = (lo + hi) // 2
                lo, hi = (mid + 1, hi) if surv(mid) > 0.01 else (lo, mid)
            k_model = lo
        ks = [1, 2, 4, 8, 16, 32, 64]
        solved_meas = [float(1 - fail_prob(counts, K, k).mean()) for k in ks]
        solved_model = [float(1 - np.mean((1 - Fbar) ** k)) for k in ks]
        solved_ind = [float(1 - (1 - pbar_ind) ** k) for k in ks]
        hz = lambda k: (float(np.mean(fail_prob(counts, K, k) - fail_prob(counts, K, k + 1)) / np.mean(fail_prob(counts, K, k)))
                        if np.mean(fail_prob(counts, K, k)) > 0 else float("nan"))
        hazard_meas = [hz(k) for k in (0, 1, 3, 7, 15, 31, 63)]
        hzm = lambda k: float(np.mean(Fbar * (1 - Fbar) ** k) / np.mean((1 - Fbar) ** k))
        hazard_model = [hzm(k) for k in (0, 1, 3, 7, 15, 31, 63)]
        # give-up rule
        def cost_model(k):
            num = np.mean([np.sum((1 - f) ** np.arange(k)) for f in Fbar]) if k < 5000 else np.mean(np.where(Fbar > 0, 1 / np.maximum(Fbar, 1e-300), np.inf))
            den = np.mean(1 - (1 - Fbar) ** k)
            return float(num / den) if den > 0 else float("inf")
        def cost_meas(k):
            num = sum(np.mean(fail_prob(counts, K, i)) for i in range(k))
            den = 1 - np.mean(fail_prob(counts, K, k))
            return float(num / den) if den > 0 else float("inf")
        grid = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64]
        cm, cmeas = {k: cost_model(k) for k in grid + [256, 1024]}, {k: cost_meas(k) for k in grid}
        kbest = min(cm, key=cm.get)
        res[eta] = {"p_measured": pbar_meas, "p_independent": pbar_ind, "p_model": float(Fbar.mean()),
                    "amplify_measured_p": amp(pbar_meas), "amplify_independent_p": amp(pbar_ind),
                    "attempts_99_model": k_model, "share_never_model": never_model,
                    "solved_k": ks, "solved_measured": solved_meas, "solved_model": solved_model, "solved_independent": solved_ind,
                    "hazard_after": [0, 1, 3, 7, 15, 31, 63], "hazard_measured": hazard_meas, "hazard_model": hazard_model,
                    "giveup_cost_model": cm, "giveup_cost_measured": cmeas, "giveup_best_k_model": kbest,
                    "cost_independent": 1 / pbar_meas}
    return res


if __name__ == "__main__":
    allres = {}
    for tag, beta, n, K in SETS:
        data = collect(tag, beta, n, K)
        np.savez_compressed(HERE / f"retry_cost_t{tag}_b{beta}_n{n}.npz",
                            **{f"{k}_{eta}": v for eta, D in data.items() for k, v in D.items()})
        res = analyse(data, K)
        allres[f"{beta},{n}"] = res
        for eta, v in res.items():
            print(f"\n{T.beta_name(beta)} n={n} eta={eta}: p measured {v['p_measured']:.4f}, model {v['p_model']:.4f}, "
                  f"estimator-style {v['p_independent']:.4f}")
            print(f"  attempts for 99%: amplify(measured p) {v['amplify_measured_p']:.1f}; amplify(estimator p) "
                  f"{v['amplify_independent_p']:.1f}; exact model {v['attempts_99_model']} "
                  f"(instances the model says are never solved: {100 * v['share_never_model']:.2f}%)")
            print("  solved within k:", "  ".join(f"k={k}: meas {100 * a:.1f}% model {100 * b:.1f}% indep {100 * c:.1f}%"
                  for k, a, b, c in zip(v["solved_k"], v["solved_measured"], v["solved_model"], v["solved_independent"])))
            print("  P(success next | k failures):", "  ".join(f"k={k}: meas {100 * a:.2f}% model {100 * b:.2f}%"
                  for k, a, b in zip(v["hazard_after"], v["hazard_measured"], v["hazard_model"])))
            print(f"  give-up after k failures, attempts per solved instance: best k (model) {v['giveup_best_k_model']}; " +
                  "  ".join(f"k={k}: model {v['giveup_cost_model'][k]:.1f} meas {v['giveup_cost_measured'].get(k, float('nan')):.1f}"
                            for k in (1, 2, 4, 8, 16, 32, 64)) + f"; never give up (model) {v['giveup_cost_model'][1024]:.1f}; "
                  f"1/p {v['cost_independent']:.1f}", flush=True)
    (HERE / "retry_cost.json").write_text(json.dumps(allres, indent=1, default=float))
