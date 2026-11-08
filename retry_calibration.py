"""Robustness check of the exact fixed-norm law (post hoc, on saved data; not pre-registered).

Two weaknesses of the earlier cell tests are addressed:
1. Instances that share a lattice share its bases, so Wilson intervals that treat all 3,200
   instances as independent are too narrow. Here every interval is a lattice-level bootstrap
   (resample the 16 lattices with replacement).
2. Cells test aggregates. Here each instance is tested on its own: given the per-attempt
   probabilities a model assigns to that instance, its success count is Poisson-binomial, and
   the randomised PIT u = P(X < c) + V*P(X = c) is Uniform(0,1) if the model is right.
   Var(u) > 1/12 means the model is under-dispersed (too few never/always-solved instances).

Models compared, both with the same mean per lattice and attempt:
- exact:  p_ij = F_ij, the exact fixed-norm law at instance i's own norm, on basis j;
- pooled: p_ij = mean over instances of F_ij (independent trials, correct mean).
Data: retry_cost_t*.npz (R8 fresh bases t7, exploratory BKZ-20 n=100 t4), from retry_cost.py.
"""
import numpy as np

FILES = {"BKZ-20 n=95 (R8)": "retry_cost_t7_b20_n95.npz",
         "BKZ-10 n=85 (R8)": "retry_cost_t7_b10_n85.npz",
         "BKZ-20 n=100 (expl.)": "retry_cost_t4_b20_n100.npz"}
B = 2000


def pit(P, c, rng):
    """Randomised PIT of counts c under independent Bernoulli(P[..., j]); P has shape (..., K)."""
    dist = np.zeros(P.shape[:-1] + (P.shape[-1] + 1,))
    dist[..., 0] = 1.0
    for j in range(P.shape[-1]):  # Poisson-binomial by dynamic programming
        p = P[..., j, None]
        dist = dist * (1 - p) + np.concatenate([np.zeros_like(dist[..., :1]), dist[..., :-1]], -1) * p
    cdf = np.cumsum(dist, -1)
    below = np.take_along_axis(cdf, c[..., None] - 1, -1)[..., 0] * (c > 0)
    at = np.take_along_axis(dist, c[..., None], -1)[..., 0]
    return below + rng.random(c.shape) * at


def boot(stat, L, rng):
    """Lattice-level bootstrap: 95% interval of stat(lattice_index_array)."""
    vals = [stat(rng.integers(0, L, L)) for _ in range(B)]
    return np.percentile(vals, [2.5, 97.5])


def main():
    rng = np.random.default_rng(1)
    print(f"Lattice-level bootstrap, {B} resamples of the 16 lattices; uniform PIT has var 1/12 = 0.0833\n")
    worst = {"exact": 0.0, "pooled": 0.0}
    for name, f in FILES.items():
        d = np.load(f)
        for eta in (2, 3):
            S, F = d[f"S_{eta}"], d[f"F_{eta}"]
            L = S.shape[0]
            c = S.sum(-1)
            Fp = np.broadcast_to(F.mean(1, keepdims=True), F.shape)
            never = (c == 0).astype(float)
            pred = {"exact": np.prod(1 - F, -1), "pooled": np.prod(1 - Fp, -1)}
            u = {"exact": pit(F, c, rng), "pooled": pit(Fp, c, rng)}
            if S.sum() < 50:
                print(f"{name} eta={eta}: skipped, {S.sum()} successes")
                continue
            print(f"{name} eta={eta}: {S.mean():.2%} per attempt, never solved in 64 measured {never.mean():.2%} "
                  f"{np.round(100 * boot(lambda ix: never[ix].mean(), L, rng), 2)}")
            for m in ("exact", "pooled"):
                dn = never - pred[m]
                ci_n = boot(lambda ix: dn[ix].mean(), L, rng)
                v = u[m].var()
                ci_v = boot(lambda ix: u[m][ix].var(), L, rng)
                ok = ci_n[0] <= 0 <= ci_n[1] and ci_v[0] <= 1 / 12 <= ci_v[1]
                worst[m] += not ok
                print(f"    {m:6s} never pred {pred[m].mean():6.2%}  diff CI {np.round(100 * ci_n, 2)} pts   "
                      f"PIT var {v:.4f} CI {np.round(ci_v, 4)}   {'ok' if ok else 'OFF'}")
    print(f"\nsettings off (never-solved diff or PIT variance CI excludes the model value): {worst}")
    return worst


def selfcheck():
    """PIT of draws from the model itself must be uniform; draws from a mixture must not be."""
    rng = np.random.default_rng(0)
    P = np.repeat(rng.uniform(0.0, 0.3, (4000, 1)), 64, 1)  # each instance has its own p
    c = (rng.random(P.shape) < P).sum(-1)
    u = pit(P, c, rng)
    assert abs(u.mean() - 0.5) < 0.02 and abs(u.var() - 1 / 12) < 0.005, (u.mean(), u.var())
    Pp = np.broadcast_to(P.mean(0, keepdims=True), P.shape)
    assert pit(Pp, c, rng).var() > 1 / 12 + 0.01  # pooling hides spread: PIT is U-shaped


if __name__ == "__main__":
    selfcheck()
    main()
