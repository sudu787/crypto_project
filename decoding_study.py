"""Decoding-step study on toy LWE: how well do success models predict nearest-plane decoding, and does
the exact centred binomial (CBD) error help choose the final candidate?

Toy parameters only (q = 3329, m = n, n = 70-100). Nothing here is a security claim about ML-KEM.

Setting. The held-out LLL/BKZ bases of toy_lwe_test.py (16 per setting, cached), targets t = (0, b) with
b = A s + e, and s, e ~ CBD(eta), eta in {2, 3}. The true offset is o = (-s, e). With unit Gram-Schmidt
directions u_i, Babai succeeds exactly when |<o, u_i>| < ||b*_i|| / 2 at every level, and Lindner-Peikert
with d_i planes keeps the true leaf exactly when |<o, u_i>| < d_i ||b*_i|| / 2 at every level.

Models of that success probability, all evaluated on the real reduced basis unless stated:
  gauss   prod_i erf(d_i ||b*_i|| / (2 sqrt2 sigma))          (Lindner-Peikert 2011, Gaussian error)
  sphere  prod_i I_x(1/2, (d-1)/2), x = d_i^2 ||b*_i||^2 / (4 d sigma^2)
          (Wunderer 2019; the lattice estimator's prob.babai with norm sqrt(d) sigma)
  cbd     Monte Carlo with fresh CBD offsets: the joint rate, and the product of per-level rates
  The estimator's own prediction on its simulated (GSA) profile comes from estimator_predictions.py.
The estimator's error then splits into (A) simulated vs real profile, (B) error law (sphere or Gaussian
vs exact CBD) and (C) independence across levels (CBD joint vs CBD product of marginals).

Rules, set before any run:
  R1 calibration. A model is "off" at a setting when its mean prediction over the 16 lattices lies outside
     the 99% Wilson interval of the measured rate. Reported for Babai and Lindner-Peikert (budgets 1024 and
     16384), for 9 (reduction, n) settings x eta in {2, 3}, 100 targets per lattice.
  R2 final candidate. On identical final lists of 3-plane pruned beam search (T in {4, 8, 12}), at LLL n=80,
     BKZ-10 n=100 and BKZ-20 n=90, 100, for eta in {2, 3}, 50 targets per lattice: CBD likelihood with a
     +-eta box, and the box followed by Euclidean distance, are each compared with Euclidean distance.
     A rule helps only if McNemar's exact test is significant at Bonferroni alpha 0.05 / 48. The share of
     targets whose true point is anywhere in the list is reported as the most any rule could gain.
  Outside the rules: per-level sum of u_ij^4 (the projection's excess kurtosis is -sum u_ij^4 / eta), as a
     check of whether some directions stay close to single coordinates.

Run on Windows with the GPU (bases must already be cached by toy_lwe_test.py --reduce):
  uv run --no-project --python 3.12 --with numpy --with scipy --with "torch==2.6.0+cu126"
    --index https://download.pytorch.org/whl/cu126 --index-strategy unsafe-best-match
    python decoding_study.py --check | --calibrate | --lists
"""
import argparse
import json
import math
import pathlib
import sys
import time

import numpy as np
import torch
from scipy.special import betainc, erf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import toy_lwe_gpu as G
import toy_lwe_test as T
import va_anp_v2 as V

HERE = pathlib.Path(__file__).resolve().parent
TAG = T.TAGS["heldout"]
COMBOS = [(2, 70), (2, 80), (10, 70), (10, 80), (10, 100), (20, 70), (20, 80), (20, 90), (20, 100)]
ETAS = (2, 3)
LATTICES = 16
LP_BUDGETS = (1024, 16384)
LIST_SETTINGS = [(2, 80), (10, 100), (20, 90), (20, 100)]
LIST_CFGS = [("beam_T", 3, t, 64) for t in (4.0, 8.0, 12.0)]
Z99 = 2.5758293035489


def wilson(k, n, z=Z99):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def cbd_logpmf(eta):
    k = np.arange(-eta, eta + 1)
    return np.log(np.array([math.comb(2 * eta, eta + int(x)) for x in k]) / 4 ** eta)


def instance(beta, n, idx, eta, count):
    """Cached reduced basis and targets. Raises if the basis isn't cached (fpylll isn't on Windows)."""
    A = T.make_A(TAG, n, n, idx)
    B, info = T.reduced(TAG, n, n, beta, idx, 0)
    Bs, nrm = T.gso(B)
    tg = T.make_targets(A, TAG, eta, idx, count)
    ts = np.stack([np.concatenate([np.zeros(n, dtype=np.int64), b]) for *_, b in tg])
    offs = np.stack([np.concatenate([-s, e]) for s, e, _ in tg])
    return A, B, Bs, nrm, ts, offs


def level_models(nrm, sigma, dvec):
    d = len(nrm)
    gauss = erf(dvec * np.sqrt(nrm) / (2 * math.sqrt(2) * sigma))
    sphere = betainc(0.5, (d - 1) / 2, np.clip(dvec ** 2 * nrm / (4 * d * sigma ** 2), 0, 1))
    return gauss, sphere


def monte_carlo(U, thresholds, eta, count, seed, gaussian=False):
    """Fresh offsets o ~ CBD(eta)^d (or N(0, eta/2) with gaussian), projected on the rows of U.
    For each threshold vector: the joint pass rate and the per-level pass rates."""
    d = U.shape[0]
    g = torch.Generator(device=G.DEV).manual_seed(seed)
    Ut = torch.as_tensor(U.T, dtype=G.F64, device=G.DEV)
    th = [torch.as_tensor(t, dtype=G.F64, device=G.DEV) for t in thresholds]
    joint = [0] * len(th)
    level = [torch.zeros(d, dtype=G.F64, device=G.DEV) for _ in th]
    done = 0
    while done < count:
        m = min(50_000, count - done)
        if gaussian:
            Z = torch.randn((m, d), generator=g, device=G.DEV, dtype=G.F64) * math.sqrt(eta / 2)
        else:
            bits = torch.randint(0, 2, (m, d, 2 * eta), generator=g, device=G.DEV, dtype=torch.int8)
            Z = (bits[..., :eta].sum(-1) - bits[..., eta:].sum(-1)).to(G.F64)
        P = (Z @ Ut).abs()
        for k, t in enumerate(th):
            ok = P < t
            joint[k] += int(ok.all(1).sum())
            level[k] += ok.sum(0)
        done += m
    return [j / count for j in joint], [(lv / count).cpu().numpy() for lv in level]


def got_flags(decoded, offs, n):
    return np.array([np.array_equal(np.rint(p[:n]).astype(np.int64), -o[:n]) for (p, *_), o in zip(decoded, offs)])


def calibrate_one(beta, n, idx, eta, count, mc):
    sigma = math.sqrt(eta / 2)
    A, B, Bs, nrm, ts, offs = instance(beta, n, idx, eta, count)
    U = Bs / np.sqrt(nrm)[:, None]
    proj = np.abs(offs @ U.T)
    decoders = {"babai": (("babai",), np.ones(len(nrm)))}
    for b in LP_BUDGETS:
        decoders[f"lp{b}"] = (("lp", b), V.lp_planes(nrm, sigma, b).astype(float))
    seed = (beta * 1000 + n) * 100 + idx * 10 + eta
    joint, level = monte_carlo(U, [dv * np.sqrt(nrm) / 2 for _, dv in decoders.values()], eta, mc, seed)
    out = {"nrm": nrm.tolist()}
    for k, (name, (cfg, dvec)) in enumerate(decoders.items()):
        decoded = G.decode_all(cfg, B, Bs, nrm, ts, sigma)
        got = got_flags(decoded, offs, n)
        passes = (proj < dvec * np.sqrt(nrm) / 2).all(1)
        if name == "babai":
            assert np.array_equal(got, passes), f"Babai identity fails: {beta} {n} {idx} {eta}"
        else:
            assert not (got & ~passes).any(), f"{name} recovered a target whose path was outside its planes"
        gauss, sphere = level_models(nrm, sigma, dvec)
        out[name] = {"got": got.tolist(), "in_leaves": passes.tolist(), "nodes": float(np.mean([x[3] for x in decoded])),
                     "gauss": float(np.prod(gauss)), "sphere": float(np.prod(sphere)), "cbd_joint": joint[k],
                     "cbd_marginals": float(np.prod(level[k])), "planes": dvec.astype(int).tolist()}
    # Where Babai fails, and how far from Gaussian the projection is there.
    s4 = (U ** 4).sum(1)
    fail = 1 - level[0]
    worst = int(np.argmax(fail))
    gauss0, _ = level_models(nrm, sigma, np.ones(len(nrm)))
    out["zshape"] = {"s4_mean": float(s4.mean()), "s4_failweighted": float((fail * s4).sum() / max(fail.sum(), 1e-300)),
                     "worst_level": worst, "worst_s4": float(s4[worst]), "worst_fail_cbd": float(fail[worst]),
                     "worst_fail_gauss": float(1 - gauss0[worst]), "fail_share_last10": float(fail[-10:].sum() / max(fail.sum(), 1e-300))}
    return out


def calibrate(args):
    path = HERE / "decoding_study_calibration.json"
    res = json.loads(path.read_text()) if path.exists() and args.resume else {}
    start = time.perf_counter()
    for beta, n in COMBOS:
        for eta in ETAS:
            key = f"{beta},{n},{eta}"
            if key in res:
                continue
            rows = [calibrate_one(beta, n, idx, eta, args.targets, args.mc) for idx in range(LATTICES)]
            res[key] = rows
            path.write_text(json.dumps(res))
            got = np.concatenate([r["babai"]["got"] for r in rows])
            print(f"  {time.perf_counter() - start:6.0f}s  {T.beta_name(beta):<7} n={n:<4} eta={eta}  Babai {100 * got.mean():5.1f}%  "
                  f"gauss {100 * np.mean([r['babai']['gauss'] for r in rows]):5.1f}  sphere {100 * np.mean([r['babai']['sphere'] for r in rows]):5.1f}  "
                  f"cbd {100 * np.mean([r['babai']['cbd_joint'] for r in rows]):5.1f}  "
                  f"LP16384 {100 * np.mean(np.concatenate([r['lp16384']['got'] for r in rows])):5.1f}%", flush=True)


def pick_rules(R, acc, eta, logpmf):
    """Index chosen by each rule on one final list."""
    euclid = int(np.argmin(acc))
    box = np.flatnonzero((np.abs(R) <= eta).all(1))
    if not len(box):
        return {"euclid": euclid, "box": euclid, "cbd": euclid}
    score = logpmf[R[box] + eta].sum(1)
    return {"euclid": euclid, "box": int(box[np.argmin(acc[box])]), "cbd": int(box[np.argmax(score)])}


def lists(args):
    path = HERE / "decoding_study_lists.json"
    res = json.loads(path.read_text()) if path.exists() and args.resume else {}
    start = time.perf_counter()
    for beta, n in LIST_SETTINGS:
        for eta in ETAS:
            logpmf = cbd_logpmf(eta)
            sigma = math.sqrt(eta / 2)
            for cfg in LIST_CFGS:
                key = f"{beta},{n},{eta},{cfg[2]}"
                if key in res:
                    continue
                flags = {k: [] for k in ("euclid", "box", "cbd", "in_list")}
                sizes, nodes, boxed = [], [], []
                for idx in range(LATTICES):
                    A, B, Bs, nrm, ts, offs = instance(beta, n, idx, eta, args.list_targets)
                    decoded = G.decode_all(cfg, B, Bs, nrm, ts, sigma, keep_all=True)
                    for ((R, acc), _, _, nd), o in zip(decoded, offs):
                        true = (R == o).all(1)
                        picks = pick_rules(R, acc, eta, logpmf)
                        for k, i in picks.items():
                            flags[k].append(bool(true[i]))
                        flags["in_list"].append(bool(true.any()))
                        sizes.append(len(R))
                        nodes.append(nd)
                        boxed.append(int((np.abs(R) <= eta).all(1).sum()))
                res[key] = {"beta": beta, "n": n, "eta": eta, "cfg": str(cfg), **flags, "list_size": float(np.mean(sizes)),
                            "boxed": float(np.mean(boxed)), "nodes": float(np.mean(nodes))}
                path.write_text(json.dumps(res))
                f = {k: 100 * np.mean(v) for k, v in flags.items()}
                print(f"  {time.perf_counter() - start:6.0f}s  {T.beta_name(beta):<7} n={n:<4} eta={eta} T={cfg[2]:<5} "
                      f"euclid {f['euclid']:5.1f}%  box {f['box']:5.1f}%  cbd {f['cbd']:5.1f}%  in list {f['in_list']:5.1f}%  "
                      f"list {np.mean(sizes):7.0f}, inside box {np.mean(boxed):6.1f}", flush=True)


def check():
    # 1. CBD sampler and the exact pmf.
    for eta in ETAS:
        d = 4
        U = np.eye(d)
        joint, level = monte_carlo(U, [np.full(d, 0.5)], eta, 200_000, 1)
        p0 = math.comb(2 * eta, eta) / 4 ** eta  # P(X = 0)
        assert abs(level[0][0] - p0) < 0.005, (level[0][0], p0)
        assert abs(np.exp(cbd_logpmf(eta)).sum() - 1) < 1e-12
    print("  CBD sampler matches P(X=0); pmf sums to 1", flush=True)
    # 2. With Gaussian offsets the Monte Carlo reproduces the erf product (independence is exact for Gaussians).
    beta, n, idx, eta = 10, 80, 0, 2
    A, B, Bs, nrm, ts, offs = instance(beta, n, idx, eta, 100)
    U = Bs / np.sqrt(nrm)[:, None]
    assert np.allclose(U @ U.T, np.eye(len(nrm)), atol=1e-8)
    gauss, sphere = level_models(nrm, math.sqrt(eta / 2), np.ones(len(nrm)))
    joint, _ = monte_carlo(U, [np.sqrt(nrm) / 2], eta, 400_000, 2, gaussian=True)
    sd = math.sqrt(np.prod(gauss) * (1 - np.prod(gauss)) / 400_000)
    assert abs(joint[0] - np.prod(gauss)) < 5 * sd, (joint[0], np.prod(gauss))
    print(f"  Gaussian Monte Carlo {joint[0]:.4f} vs erf product {np.prod(gauss):.4f}", flush=True)
    # 3. The Babai identity, and Euclidean picks on full lists equal the decoder's own picks.
    row = calibrate_one(beta, n, idx, eta, 100, 50_000)
    print(f"  Babai identity holds on 100 targets ({100 * np.mean(row['babai']['got']):.0f}% recovered)", flush=True)
    for cfg in LIST_CFGS[:2] + [("beam", 3, 4), ("babai",)]:
        own = G.decode_all(cfg, B, Bs, nrm, ts, 1.0)
        full = G.decode_all(cfg, B, Bs, nrm, ts, 1.0, keep_all=True)
        for (p, *_), ((R, acc), _, _, nd), t, (_, _, _, nd0) in zip(own, full, ts, own):
            assert np.array_equal(np.rint(t - p).astype(np.int64), R[np.argmin(acc)]) and nd == nd0, cfg
            assert np.allclose((R.astype(float) ** 2).sum(1), acc), "acc isn't the squared length"
    print("  keep_all lists: Euclidean pick equals the decoder's pick; acc equals squared length", flush=True)
    print("  all checks passed", flush=True)


def dump_profiles():
    """Real Gram-Schmidt profiles for estimator_predictions.py (checks its formula against ours)."""
    out = {}
    for beta, n in COMBOS:
        for idx in range(LATTICES):
            _, nrm = T.gso(T.reduced(TAG, n, n, beta, idx, 0)[0])
            out[f"{beta},{n},{idx}"] = nrm.tolist()
    (HERE / "decoding_study_profiles.json").write_text(json.dumps(out))
    print(f"  wrote {len(out)} profiles", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--profiles", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--lists", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--targets", type=int, default=100)
    ap.add_argument("--list-targets", type=int, default=50)
    ap.add_argument("--mc", type=int, default=200_000)
    a = ap.parse_args()
    if a.check:
        check()
    if a.profiles:
        dump_profiles()
    if a.calibrate:
        calibrate(a)
    if a.lists:
        lists(a)
