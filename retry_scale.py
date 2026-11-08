"""Scale-up of the R8 claim to larger lattices (item 1 of the follow-up plan).

Claim under test (unchanged from R8): for BKZ-reduced bases, repeated Babai attempts on one LWE instance are
independent given ||o|| and follow the exact fixed-norm law (retry_study.exact_curve); the estimator's independent
model (one radius sqrt(d) sigma) is not.

--probe     WSL: reduce ONE basis per candidate (beta, n) on probe instances (tag 9, never used in a test), to time
            BKZ and see each basis profile. Only profiles are looked at, never a decoding outcome.
--predict   GPU: predicted success per attempt (exact law at the expected norm d*eta/2) on each probe basis, so the
            test settings can be chosen in the 1-30% band, as R8's were.
--reduce    WSL: the test bases (tag 10).
--test      GPU: rule R10 below.

Probe results (one basis each, tag 9; BKZ 2.0 with the fplll default strategies; long double below d = 240,
double-double from d = 240): seconds per basis and exact-law success per attempt at the expected norm.
  BKZ-30 n=120   83s  eta=1 0.68%   eta=2 0.00%
  BKZ-40 n=120  115s  eta=1 19.1%   eta=2 0.59%   eta=3 0.02%
  BKZ-30/40/50 n=150 (238/288/1244s) and BKZ-40/50 n=200 (758/2350s): Babai success ~0 at every eta. The first
  basis vector stays a q-vector there (root-Hermite factor equals the q-vector value), so Babai is not a usable
  decoder at these sizes with this machine's BKZ budget.
Hence the scale-up uses Babai at n = 120 and pruned enumeration (whose success condition is evaluated at any size,
see retry_enum.py) at n = 150. n = 200 is left out (about 7 hours more of BKZ for one setting).

R10 (fixed 8 Nov 2026, before any tag-10 basis was reduced). Fresh instances (tag 10), 16 lattices x 200 targets,
    same permutation re-randomisation, BKZ 2.0 reduction as in the probes (time limit 3600 s; any run that hits it is
    reported).
    (a) Babai, BKZ-40 n=120, K=64, eta in {1, 2}. Same 8 cells and 99% Wilson intervals as R8. The exact fixed-norm law
        is off in at most 2 cells and in fewer than the independent model, and its predicted count variance is within
        25% of measured in every (eta) with at least 50 successes (degeneracy guard as in R8).
    (b) Enumeration with linear pruning, R^2 = 1.1 d sigma^2, BKZ-40 n=150, K=32, eta in {1, 2}. Independence rejected
        (R4 permutation test, p < 0.01) at each eta with at least 50 successes; the fixed-norm law G off in at most 2 of
        the 8 cells and in fewer than the independent model.
    R10 passes if (a) and (b) both pass. Reported either way.
"""
import argparse
import json
import math
import os
import pathlib
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import retry_study as R  # noqa: E402
import toy_lwe_test as T  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TAG, TEST_TAG = 9, 10
CANDIDATES = [(30, 120), (40, 120), (30, 150), (40, 150), (50, 150), (40, 200), (50, 200)]


def reduce_big(A, beta, time_limit):
    """As toy_lwe_test.reduce_basis, but double-double floats from d = 240 (long double aborts there)."""
    from fpylll import BKZ, LLL, IntegerMatrix
    B0 = T.q_basis(A)
    d = B0.shape[0]
    ft = "ld" if d < 240 else "dd"
    M = IntegerMatrix.from_matrix(B0.tolist())
    start = time.perf_counter()
    LLL.reduction(M)
    # The pip wheel's built-in strategy path does not exist; the conda fplll copy is used (BKZ 2.0 pruning).
    strat = os.environ.get("FPLLL_STRATEGY", "/home/sudu/micromamba/envs/sage/share/fplll/strategies/default.json")
    p = BKZ.Param(block_size=beta, strategies=strat,
                  flags=BKZ.AUTO_ABORT | BKZ.MAX_LOOPS | BKZ.MAX_TIME, max_loops=16, max_time=time_limit)
    BKZ.reduction(M, p, float_type=ft)
    info = {"float": ft, "seconds": time.perf_counter() - start}
    info["hit_limit"] = info["seconds"] >= time_limit
    return np.array([[M[i, j] for j in range(d)] for i in range(d)], dtype=np.int64), info


def path_for(tag, beta, n, idx, j):
    return R.RETRY / f"t{tag}_b{beta}_n{n}_i{idx}_j{j}.npy"


def one(tag, beta, n, idx, j, limit):
    """Child process: one reduction (an fplll abort kills only this process)."""
    p = path_for(tag, beta, n, idx, j)
    if p.exists():
        return
    R.TAG = tag
    Pp, Qp = R.perms(n, idx, j)
    B, info = reduce_big(T.make_A(tag, n, n, idx)[Qp][:, Pp], beta, limit)
    tmp = p.with_name(p.stem + f".{os.getpid()}.tmp.npy")
    np.save(tmp, B)
    tmp.replace(p)
    (p.with_suffix(".json")).write_text(json.dumps(info))


def run_children(jobs, workers, limit):
    """jobs: (tag, beta, n, idx, j). Each in its own process; failures are logged, not fatal."""
    R.RETRY.mkdir(parents=True, exist_ok=True)
    todo = [jb for jb in jobs if not path_for(*jb).exists()]
    running, done, t0 = [], 0, time.perf_counter()
    while todo or running:
        while todo and len(running) < workers:
            jb = todo.pop(0)
            cmd = [sys.executable, __file__, "--one", json.dumps(list(jb) + [limit])]
            running.append((jb, subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)))
        time.sleep(2)
        for jb, pr in running[:]:
            if pr.poll() is not None:
                running.remove((jb, pr))
                done += 1
                ok = path_for(*jb).exists()
                secs = json.loads(path_for(*jb).with_suffix(".json").read_text())["seconds"] if ok else float("nan")
                err = "" if ok else pr.stderr.read().decode(errors="replace").strip().splitlines()[-1:]
                print(f"  [{done}/{done + len(todo) + len(running)}] {time.perf_counter() - t0:7.0f}s  t{jb[0]} BKZ-{jb[1]} "
                      f"n={jb[2]} lattice {jb[3]} basis {jb[4]}: {'%.0fs' % secs if ok else 'FAILED ' + str(err)}", flush=True)


def predict():
    import toy_lwe_gpu as G  # noqa: F401  (GPU)
    rows = []
    for beta, n in CANDIDATES:
        p = path_for(PROBE_TAG, beta, n, 0, 0)
        if not p.exists():
            print(f"BKZ-{beta} n={n}: no probe basis")
            continue
        info = json.loads(p.with_suffix(".json").read_text())
        _, nrm = T.gso(np.load(p))
        d = 2 * n
        pr = {eta: float(R.exact_curve(nrm, [d * eta / 2], 200_000, seed=beta * 1000 + n)[0]) for eta in (1, 2, 3)}
        delta = (math.sqrt(nrm[0]) / math.exp(np.log(nrm).sum() / (2 * d))) ** (1 / d)
        rows.append({"beta": beta, "n": n, "seconds": info["seconds"], "hit_limit": info["hit_limit"], "delta": delta,
                     "p_attempt": pr})
        print(f"BKZ-{beta} n={n}: {info['seconds']:.0f}s{' (time limit)' if info['hit_limit'] else ''}, delta {delta:.5f}, "
              + "  ".join(f"eta={e}: {100 * v:.2f}%" for e, v in pr.items()), flush=True)
    (HERE / "retry_scale_probe.json").write_text(json.dumps(rows, indent=1))


BABAI_SET, ENUM_SET, ETAS10 = (40, 120, 64), (40, 150, 32), (1, 2)


def test():
    import retry_enum as E
    import retry_exact as X
    R.ETAS = ETAS10
    beta, n, K = BABAI_SET
    res_a = X.run([BABAI_SET], TEST_TAG, "R10a")  # final R6-style verdict inside run() is not used
    rows = {k: v for k, v in res_a.items() if k != "verdict"}
    succ = {k: r["mean_success"] * r["K"] * R.LATTICES * R.TARGETS for k, r in rows.items()}
    degenerate = [k for k, v in succ.items() if v < 50]
    var_ok = all(abs(r["models"]["exact"]["var"] / r["count_var"] - 1) <= 0.25 for k, r in rows.items() if k not in degenerate)
    offs = {m: sum(c["off"] for r in rows.values() for c in r["models"][m]["cells"]) for m in ("independent", "exact")}
    a_pass = offs["exact"] <= 2 and offs["exact"] < offs["independent"] and var_ok and len(degenerate) <= 1
    print("R10a verdict:", {"off": offs, "degenerate": degenerate, "successes": succ, "var_ok": var_ok, "pass": a_pass}, flush=True)
    res_b = E.test(sets=[ENUM_SET], tag=TEST_TAG, etas=ETAS10, label="R10b", outfile="retry_scale_enum.json")
    b_pass = res_b["verdict"]["R12_pass"]
    verdict = {"R10a_pass": a_pass, "R10b_pass": b_pass, "R10_pass": a_pass and b_pass, "R10a_off": offs, "R10a_degenerate": degenerate}
    print("R10 verdict:", verdict, flush=True)
    (HERE / "retry_scale.json").write_text(json.dumps({"babai": res_a, "enum": res_b, "verdict": verdict}, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--one")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--predict", action="store_true")
    ap.add_argument("--reduce", action="store_true")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--limit", type=int, default=3600)
    a = ap.parse_args()
    if a.one:
        one(*json.loads(a.one))
    if a.probe:
        run_children([(PROBE_TAG, b, n, 0, 0) for b, n in CANDIDATES], a.workers, a.limit)
    if a.predict:
        predict()
    if a.reduce:  # enumeration set first (slower bases), then Babai set
        jobs = [(TEST_TAG, b, n, i, j) for b, n, K in (ENUM_SET, BABAI_SET) for i in range(R.LATTICES) for j in range(K)]
        run_children(jobs, a.workers, a.limit)
    if a.test:
        test()
