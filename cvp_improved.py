"""
==============================================================================
Improved CVP Decoding Experiment for Lattice-Based Cryptography
==============================================================================

WHAT THIS DOES:
  Compares CVP/BDD decoding strategies on q-ary lattices relevant to
  lattice-based cryptographic schemes (like ML-KEM / CRYSTALS-Kyber).

ALGORITHMS COMPARED:
  1. Babai Round-Off (baseline)
  2. Babai Nearest Plane (standard)
  3. Lindner-Peikert Nearest Planes (LP, proper implementation)
  4. Adaptive Nearest Planes (ANP) - our optimization of LP
     Key idea: Measure rounding ambiguity per dimension, branch only
     where the fractional part is close to 0.5. This is a known
     optimization in the MIMO detection literature, adapted here for
     the lattice-crypto BDD setting.

HONEST FRAMING:
  - The idea of selective/adaptive branching is NOT novel in the
    literature (it appears in MIMO detection, enumeration pruning, etc.)
  - Our contribution is: a clean implementation with systematic
    benchmarking showing the speed-accuracy tradeoff in the lattice-crypto
    context, with a proper comparison methodology.
==============================================================================
"""

import numpy as np
from numpy.linalg import norm
import time
import sys


np.random.seed(42)


# ============================================================================
# LATTICE UTILITIES
# ============================================================================

def gram_schmidt(B):
    """Gram-Schmidt orthogonalization of basis B (rows are vectors)."""
    n = B.shape[0]
    B_star = np.zeros_like(B, dtype=float)
    mu = np.zeros((n, n), dtype=float)

    for i in range(n):
        B_star[i] = B[i].copy()
        for j in range(i):
            nrm = np.dot(B_star[j], B_star[j])
            if nrm < 1e-10:
                mu[i][j] = 0
            else:
                mu[i][j] = np.dot(B[i], B_star[j]) / nrm
            B_star[i] -= mu[i][j] * B_star[j]

    return B_star, mu


def lll_reduce(B, delta=0.75):
    """LLL lattice basis reduction."""
    n = B.shape[0]
    B = B.astype(float).copy()
    B_star, mu = gram_schmidt(B)

    k = 1
    while k < n:
        for j in range(k - 1, -1, -1):
            if abs(mu[k][j]) > 0.5:
                B[k] -= round(mu[k][j]) * B[j]
                B_star, mu = gram_schmidt(B)

        lhs = np.dot(B_star[k], B_star[k])
        rhs = (delta - mu[k][k-1]**2) * np.dot(B_star[k-1], B_star[k-1])

        if lhs >= rhs:
            k += 1
        else:
            B[[k, k-1]] = B[[k-1, k]]
            B_star, mu = gram_schmidt(B)
            k = max(k - 1, 1)

    return B


def generate_qary_lattice(n, q=3329):
    """Generate q-ary lattice basis mimicking LWE/ML-KEM structure.
    
    The lattice is:
      L = { x in Z^n : A*x_1 = x_2 mod q }
    represented as a basis with qI in the top-left block.
    """
    k = n // 2
    A = np.random.randint(0, q, size=(n - k, k))

    B = np.zeros((n, n), dtype=float)
    B[:k, :k] = q * np.eye(k)
    B[k:, :k] = A
    B[k:, k:] = np.eye(n - k)

    return B


def generate_bdd_instance(B, noise_std):
    """Generate a BDD instance: target = lattice_point + small_noise.
    
    This models the decryption scenario: the ciphertext encodes a lattice
    point plus small error, and the decoder must recover the lattice point.
    """
    n = B.shape[0]
    coeffs = np.random.randint(-3, 4, size=n)
    lattice_point = coeffs @ B
    noise = np.random.normal(0, noise_std, size=n)
    target = lattice_point + noise
    return target, lattice_point, coeffs


# ============================================================================
# CVP ALGORITHM 1: Babai Round-Off
# ============================================================================

def babai_roundoff(B, target):
    """Babai's Round-Off on the given basis.
    
    Computes B^{-1} * target and rounds each coordinate.
    Works best with a well-reduced basis.
    """
    start = time.perf_counter()
    # Use least-squares solve for numerical stability
    coords = np.linalg.solve(B.T @ B, B.T @ target)
    rounded = np.round(coords).astype(int)
    closest = rounded @ B
    return closest, time.perf_counter() - start


# ============================================================================
# CVP ALGORITHM 2: Babai Nearest Plane
# ============================================================================

def babai_nearest_plane(B_star, mu, B, target):
    """Standard Babai Nearest Plane using pre-computed GS basis."""
    start = time.perf_counter()
    n = B.shape[0]
    b = target.copy().astype(float)

    for i in range(n - 1, -1, -1):
        nrm_sq = np.dot(B_star[i], B_star[i])
        if nrm_sq < 1e-10:
            continue
        c = np.dot(b, B_star[i]) / nrm_sq
        b -= round(c) * B[i]

    closest = target - b
    return closest, time.perf_counter() - start


# ============================================================================
# CVP ALGORITHM 3: Lindner-Peikert Nearest Planes (Proper Implementation)
# ============================================================================

def lindner_peikert(B_star, mu, B, target, num_planes=2, max_list=None):
    """Lindner-Peikert nearest planes decoding.
    
    At EVERY dimension, explores 'num_planes' nearest integer planes.
    Maintains a list of candidate partial solutions, pruned to max_list.
    
    This is a proper beam search: at each level, every candidate generates
    num_planes children, then the list is pruned back.
    
    Args:
        B_star: Gram-Schmidt basis
        mu: GSO coefficients
        B: Original (reduced) basis
        target: Target vector
        num_planes: Number of planes to explore per dimension (k in LP)
        max_list: Maximum candidates to maintain (default: num_planes * n)
    """
    start = time.perf_counter()
    n = B.shape[0]
    if max_list is None:
        max_list = num_planes * n

    # Each candidate: (residual_vector, accumulated_projected_distance)
    candidates = [(target.copy().astype(float), 0.0)]

    for i in range(n - 1, -1, -1):
        b_star_i = B_star[i]
        nrm_sq = np.dot(b_star_i, b_star_i)

        if nrm_sq < 1e-10:
            continue

        new_candidates = []
        for (b, acc_dist) in candidates:
            c = np.dot(b, b_star_i) / nrm_sq
            c_round = round(c)
            frac = c - c_round

            # Generate num_planes choices sorted by distance to c
            # The nearest integer is c_round, next is c_round+1 or c_round-1
            choices = [c_round]
            if frac >= 0:
                for offset in range(1, num_planes):
                    choices.append(c_round + offset)
                    if len(choices) >= num_planes:
                        break
            else:
                for offset in range(1, num_planes):
                    choices.append(c_round - offset)
                    if len(choices) >= num_planes:
                        break

            for c_try in choices:
                frac_try = c - c_try
                d = (frac_try ** 2) * nrm_sq
                new_b = b - c_try * B[i]
                new_candidates.append((new_b, acc_dist + d))

        # Prune by accumulated projected distance
        new_candidates.sort(key=lambda x: x[1])
        candidates = new_candidates[:max_list]

    # Return best by actual residual norm
    best_b, _ = min(candidates, key=lambda x: norm(x[0]))
    closest = target - best_b
    return closest, time.perf_counter() - start


# ============================================================================
# CVP ALGORITHM 4: Adaptive Nearest Planes (ANP) - Our Optimization
# ============================================================================

def adaptive_nearest_planes(B_star, mu, B, target, 
                            ambiguity_threshold=0.35,
                            branch_planes=2,
                            max_list=None):
    """Adaptive Nearest Planes (ANP) decoding.
    
    Optimization of Lindner-Peikert that concentrates computational effort
    on dimensions where rounding is ambiguous.
    
    For each dimension i, we compute the fractional part f = c_i - round(c_i).
    The "ambiguity" is 2*|f| (ranges from 0 to 1):
      - ambiguity ≈ 0: c_i is very close to an integer → greedy rounding is safe
      - ambiguity ≈ 1: c_i is near a half-integer → rounding is a coin flip
    
    We only branch (explore multiple planes) when ambiguity > threshold.
    
    This is NOT a novel idea — it's well-known in MIMO detection literature
    as "reliability-based" or "adaptive" SIC decoding. Our contribution is
    a clean implementation and systematic evaluation in the lattice-crypto
    BDD context.
    
    Args:
        B_star: Gram-Schmidt basis
        mu: GSO coefficients
        B: Original (reduced) basis
        target: Target vector
        ambiguity_threshold: Branch only when 2*|frac| > this threshold
        branch_planes: Number of planes when branching
        max_list: Max candidates (default: 2 * n)
    """
    start = time.perf_counter()
    n = B.shape[0]
    if max_list is None:
        max_list = 2 * n

    # Each candidate: (residual_vector, accumulated_projected_distance)
    candidates = [(target.copy().astype(float), 0.0)]
    
    stats = {"branched": 0, "greedy": 0}

    for i in range(n - 1, -1, -1):
        b_star_i = B_star[i]
        nrm_sq = np.dot(b_star_i, b_star_i)

        if nrm_sq < 1e-10:
            continue

        new_candidates = []

        for (b, acc_dist) in candidates:
            c = np.dot(b, b_star_i) / nrm_sq
            c_round = round(c)
            frac = c - c_round  # in [-0.5, 0.5]
            ambiguity = 2.0 * abs(frac)  # in [0, 1]

            if ambiguity <= ambiguity_threshold:
                # LOW AMBIGUITY: greedy rounding (like Babai)
                d = (frac ** 2) * nrm_sq
                new_b = b - c_round * B[i]
                new_candidates.append((new_b, acc_dist + d))
                stats["greedy"] += 1
            else:
                # HIGH AMBIGUITY: explore multiple planes (like LP)
                stats["branched"] += 1
                
                choices = [c_round]
                if frac >= 0:
                    choices.append(c_round + 1)
                    if branch_planes >= 3:
                        choices.append(c_round - 1)
                else:
                    choices.append(c_round - 1)
                    if branch_planes >= 3:
                        choices.append(c_round + 1)

                for c_try in choices[:branch_planes]:
                    frac_try = c - c_try
                    d = (frac_try ** 2) * nrm_sq
                    new_b = b - c_try * B[i]
                    new_candidates.append((new_b, acc_dist + d))

        # Prune by accumulated projected distance (same as LP — no ad-hoc scoring)
        if len(new_candidates) > max_list:
            new_candidates.sort(key=lambda x: x[1])
            candidates = new_candidates[:max_list]
        else:
            candidates = new_candidates

    # Return best by actual residual norm
    best_b, _ = min(candidates, key=lambda x: norm(x[0]))
    closest = target - best_b
    elapsed = time.perf_counter() - start
    return closest, elapsed, stats


# ============================================================================
# EXPERIMENT
# ============================================================================

def run_experiment():
    """Run the comparison experiment."""
    
    print("=" * 72)
    print("  CVP/BDD Decoding Comparison on q-ary Lattices")
    print("  (Relevant to lattice-based cryptography like ML-KEM)")
    print("=" * 72)
    print()
    print("Algorithms:")
    print("  1. Babai Round-Off (on reduced basis)")
    print("  2. Babai Nearest Plane")
    print("  3. Lindner-Peikert k=2 (branch everywhere)")
    print("  4. Lindner-Peikert k=3 (branch everywhere)")
    print("  5. Adaptive NP k=2, t=0.35 (branch only when ambiguous)")
    print("  6. Adaptive NP k=2, t=0.20 (branch more aggressively)")
    print()

    dimensions = [6, 8, 10, 12]
    noise_levels = [20, 60, 120]
    num_trials = 30
    q = 3329

    print(f"Config: dims={dimensions}, noise_s={noise_levels}, "
          f"trials={num_trials}, q={q}")
    print()

    all_results = {}

    for dim in dimensions:
        for noise_std in noise_levels:
            key = f"n={dim}, s={noise_std}"
            
            methods = {
                "Babai-RO":    {"dists": [], "times": [], "exact": 0},
                "Babai-NP":    {"dists": [], "times": [], "exact": 0},
                "LP(k=2)":     {"dists": [], "times": [], "exact": 0},
                "LP(k=3)":     {"dists": [], "times": [], "exact": 0},
                "ANP(t=.35)":  {"dists": [], "times": [], "exact": 0,
                                "branched": 0, "greedy": 0},
                "ANP(t=.20)":  {"dists": [], "times": [], "exact": 0,
                                "branched": 0, "greedy": 0},
            }

            for trial in range(num_trials):
                # Generate lattice and LLL-reduce it
                B_raw = generate_qary_lattice(dim, q)
                B_lll = lll_reduce(B_raw.copy())
                B_star, mu_mat = gram_schmidt(B_lll)

                target, true_closest, _ = generate_bdd_instance(B_raw, noise_std)

                # --- Babai Round-Off (on REDUCED basis — fair comparison) ---
                approx, t = babai_roundoff(B_lll, target)
                d = norm(approx - true_closest)
                methods["Babai-RO"]["dists"].append(d)
                methods["Babai-RO"]["times"].append(t)
                methods["Babai-RO"]["exact"] += int(d < 1e-3)

                # --- Babai Nearest Plane ---
                approx, t = babai_nearest_plane(B_star, mu_mat, B_lll, target)
                d = norm(approx - true_closest)
                methods["Babai-NP"]["dists"].append(d)
                methods["Babai-NP"]["times"].append(t)
                methods["Babai-NP"]["exact"] += int(d < 1e-3)

                # --- LP k=2 ---
                approx, t = lindner_peikert(B_star, mu_mat, B_lll, target,
                                            num_planes=2)
                d = norm(approx - true_closest)
                methods["LP(k=2)"]["dists"].append(d)
                methods["LP(k=2)"]["times"].append(t)
                methods["LP(k=2)"]["exact"] += int(d < 1e-3)

                # --- LP k=3 ---
                approx, t = lindner_peikert(B_star, mu_mat, B_lll, target,
                                            num_planes=3)
                d = norm(approx - true_closest)
                methods["LP(k=3)"]["dists"].append(d)
                methods["LP(k=3)"]["times"].append(t)
                methods["LP(k=3)"]["exact"] += int(d < 1e-3)

                # --- ANP t=0.35 ---
                approx, t, st = adaptive_nearest_planes(
                    B_star, mu_mat, B_lll, target,
                    ambiguity_threshold=0.35, branch_planes=2)
                d = norm(approx - true_closest)
                methods["ANP(t=.35)"]["dists"].append(d)
                methods["ANP(t=.35)"]["times"].append(t)
                methods["ANP(t=.35)"]["exact"] += int(d < 1e-3)
                methods["ANP(t=.35)"]["branched"] += st["branched"]
                methods["ANP(t=.35)"]["greedy"] += st["greedy"]

                # --- ANP t=0.20 ---
                approx, t, st = adaptive_nearest_planes(
                    B_star, mu_mat, B_lll, target,
                    ambiguity_threshold=0.20, branch_planes=2)
                d = norm(approx - true_closest)
                methods["ANP(t=.20)"]["dists"].append(d)
                methods["ANP(t=.20)"]["times"].append(t)
                methods["ANP(t=.20)"]["exact"] += int(d < 1e-3)
                methods["ANP(t=.20)"]["branched"] += st["branched"]
                methods["ANP(t=.20)"]["greedy"] += st["greedy"]

            # Print results for this config
            print(f"\n{'-'*72}")
            print(f"  {key}")
            print(f"{'-'*72}")

            babai_np_avg = np.mean(methods["Babai-NP"]["dists"])
            lp2_avg = np.mean(methods["LP(k=2)"]["dists"])
            lp2_time = np.mean(methods["LP(k=2)"]["times"]) * 1000

            header = (f"  {'Method':<14} {'Exact%':>7} {'AvgDist':>10} "
                      f"{'Time(ms)':>10} {'vs BNP':>8} {'vs LP2':>8}")
            print(header)
            print(f"  {'-'*62}")

            for name, m in methods.items():
                avg_d = np.mean(m["dists"])
                avg_t = np.mean(m["times"]) * 1000
                exact = m["exact"] / num_trials * 100

                vs_bnp = ((babai_np_avg - avg_d) / babai_np_avg * 100
                          if babai_np_avg > 1e-10 else 0)
                vs_lp2 = ((lp2_avg - avg_d) / lp2_avg * 100
                          if lp2_avg > 1e-10 else 0)

                marker = ""
                if "ANP" in name:
                    total = m["branched"] + m["greedy"]
                    br_pct = m["branched"] / total * 100 if total > 0 else 0
                    marker = f"  [br={br_pct:.0f}%]"

                print(f"  {name:<14} {exact:>6.1f}% {avg_d:>10.2f} "
                      f"{avg_t:>9.3f}ms {vs_bnp:>+7.1f}% {vs_lp2:>+7.1f}%{marker}")

            all_results[key] = {
                name: {
                    "avg_dist": float(np.mean(m["dists"])),
                    "avg_time_ms": float(np.mean(m["times"]) * 1000),
                    "exact_pct": float(m["exact"] / num_trials * 100),
                }
                for name, m in methods.items()
            }

    # Summary
    print(f"\n\n{'='*72}")
    print("  SUMMARY")
    print(f"{'='*72}")
    print()
    print("Key question: Does Adaptive NP achieve similar accuracy to LP")
    print("while being faster (fewer total candidates generated)?")
    print()

    for name in ["LP(k=2)", "LP(k=3)", "ANP(t=.35)", "ANP(t=.20)"]:
        avg_imp = []
        avg_time_ratio = []
        for key in all_results:
            bnp = all_results[key]["Babai-NP"]["avg_dist"]
            this = all_results[key][name]["avg_dist"]
            bnp_t = all_results[key]["Babai-NP"]["avg_time_ms"]
            this_t = all_results[key][name]["avg_time_ms"]
            if bnp > 1e-10:
                avg_imp.append((bnp - this) / bnp * 100)
            if bnp_t > 0:
                avg_time_ratio.append(this_t / bnp_t)

        print(f"  {name:<14}: avg improvement over Babai NP = "
              f"{np.mean(avg_imp):+.2f}%, "
              f"time ratio = {np.mean(avg_time_ratio):.1f}x")

    print()
    print("=" * 72)
    print("  DONE")
    print("=" * 72)


if __name__ == "__main__":
    run_experiment()
