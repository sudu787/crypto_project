"""Does VA-ANP beat a tuned ANP at any single noise level?

Pooled results can hide this: VA-ANP adapts to sigma, ANP uses one threshold everywhere.
Thresholds are picked on a tuning set and scored on a held-out set. "Work" is total planes
explored, which is deterministic; times are noisy.

Run with the same uv command as stress_test_va_anp.py.
"""
import stress_test_va_anp as S

RATIOS = [0.10, 0.14, 0.18, 0.21, 0.24, 0.27, 0.30]
ANP = {f"ANP thr={t}": (lambda i, t=t: S.run_anp(i, t))
       for t in (0.35, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95)}
VA = "VA llr=2.2"
ALGOS = {**ANP, VA: S.run_va, "VA llr=1.5": lambda i: S.run_va(i, llr=1.5),
         "VA llr=3.0": lambda i: S.run_va(i, llr=3.0)}


def by_noise(seeds):
    insts = S.bank(seeds, ratios=RATIOS)
    return {r: S.evaluate(ALGOS, [i for i in insts if i["ratio"] == r]) for r in RATIOS}


def acc(res, k):
    return sum(res[r][k]["ok"].sum() for r in res) / sum(len(res[r][k]["ok"]) for r in res)


def work(res, k):
    return sum(res[r][k]["ch"] for r in res)


def cheapest_reaching(res, target):
    ok = [k for k in ANP if acc(res, k) >= target]
    return min(ok, key=lambda k: work(res, k)) if ok else max(ANP, key=lambda k: acc(res, k))


def compare(r, name, test):
    a, v = test[r][name], test[r][VA]
    x, y, p = S.mcnemar(a["ok"], v["ok"])
    print(f"  {r:<6} {name:<14} {a['ok'].mean() * 100:6.1f}% {v['ok'].mean() * 100:6.1f}%  "
          f"{a['ch'] / a['nd']:5.2f} {v['ch'] / v['nd']:5.2f}  {a['ch'] / v['ch']:5.2f}x "
          f"{a['t'].sum() / v['t'].sum():5.2f}x  {x:3}/{y:<3} p={p:.4f}", flush=True)


if __name__ == "__main__":
    S.exp0()  # stops here if the harness no longer matches the notebook
    print("\nBuilding tuning and held-out sets (4200 each)", flush=True)
    tune, test = by_noise(range(600, 605)), by_noise(range(605, 610))

    print("\nHeld-out curves per noise: accuracy, ms, planes per node")
    for r in RATIOS:
        print(f" noise={r}")
        for k, v in test[r].items():
            S.line(k, v)

    target = acc(tune, VA)
    pick = cheapest_reaching(tune, target)
    print(f"\n[1] One fixed ANP threshold vs VA llr=2.2 (picked on tuning set: {pick})")
    print(f"    tuning accuracy: VA {target * 100:.1f}%, ANP {acc(tune, pick) * 100:.1f}%; "
          f"held-out: VA {acc(test, VA) * 100:.1f}%, ANP {acc(test, pick) * 100:.1f}%")
    print("  noise  ANP            ANPacc  VAacc  ANPpl VApl   work   time   ANP-only/VA-only")
    for r in RATIOS:
        compare(r, pick, test)
    print(f"  all    work {work(test, pick) / work(test, VA):.2f}x")

    print("\n[2] ANP threshold re-picked at each noise level, to match VA accuracy there")
    print("  noise  ANP            ANPacc  VAacc  ANPpl VApl   work   time   ANP-only/VA-only")
    for r in RATIOS:
        one = {r: tune[r]}
        compare(r, cheapest_reaching(one, acc(one, VA)), test)
