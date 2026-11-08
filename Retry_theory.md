# Why repeated decoding attempts are dependent: three short results

This note supports `Retry_study_summary.md`. It turns the measurements into statements with proofs. Every statement is checked numerically on real reduced bases by `theory_check.py`, whose output is in `theory_check_log.txt`.

## Setting

- Take a basis B of a d-dimensional lattice, with Gram–Schmidt vectors b\*\_i, unit vectors u\_i = b\*\_i/‖b\*\_i‖, and half-widths c\_i = ‖b\*\_i‖/2.
- For an LWE instance with offset o = (−s, e), Babai's nearest plane returns the right answer **iff |⟨o, u\_i⟩| < c\_i for every i**. This is Liu–Nguyen 2013, eq. (1).

**Assumption A (random direction).** Re-randomising and re-reducing the basis makes the direction of o, in the Gram–Schmidt frame, uniform on the sphere S^{d−1}. This holds independently for each attempt, while ‖o‖ stays the instance's own.

The pre-registered test R8 supports Assumption A for BKZ bases. Tests R6 and R9 show it fails in part for LLL bases.

**Definitions.** For r > 0, with z uniform on S^{d−1}:
- **F\_B(r)** = P(r·z\_i² < c\_i² for all i). This is the exact fixed-norm law, the success probability of one attempt on an instance with ‖o‖² = r.
- **Π\_B(r)** = ∏\_i P(r·z\_i² < c\_i²) = ∏\_i I\_{c\_i²/r}(1/2, (d−1)/2). This is the per-level product, which is the lattice estimator's `prob.babai` evaluated at radius √r.

Both functions are non-increasing in r.

## P1. For a fixed instance, the per-level product is biased upward

**Proposition 1.** F\_B(r) ≤ Π\_B(r) for every basis B and every r.

**Proof.**
1. Write A\_i = {|z\_i| < t\_i} with t\_i = c\_i/√r. It is enough to show P(A\_i ∩ A\_S) ≤ P(A\_i)·P(A\_S) for any index set S with i ∉ S. The result then follows by induction on |S|.
2. Condition on z\_i² = x. The other coordinates are distributed as √(1−x)·w, with w uniform on S^{d−2}.
3. So g(x) := P(A\_S | z\_i² = x) = P(|w\_j| < t\_j/√(1−x) for all j ∈ S). This is non-decreasing in x: a larger x shrinks the other coordinates.
4. P(A\_i ∩ A\_S) = E[1{z\_i² < t\_i²}·g(z\_i²)]. The first factor is non-increasing in z\_i² and the second is non-decreasing.
5. By Chebyshev's association inequality for two oppositely monotone functions of one variable, this is at most P(A\_i)·E[g(z\_i²)] = P(A\_i)·P(A\_S). ∎

**Remark.** This is the negative dependence of (z\_1², …, z\_d²), which follow a Dirichlet(½, …, ½) law. The proof above is self-contained. Intuitively, at a fixed norm, a small component in one direction forces larger components elsewhere.

**Check.** On four real bases, 33 radii each in [0.6, 1.4]·dσ², there are 0 violations beyond Monte Carlo error. Where Π > 10⁻⁴, the ratio Π/F lies in:

| Basis | Π/F |
|---|---|
| BKZ-20, n = 95 | 1.007–1.123 |
| BKZ-10, n = 85 | 1.004–1.084 |
| BKZ-20, n = 100 | 1.038–1.268 |
| LLL, n = 78 | 1.044–1.294 |

This is the 4–33% upward bias of the product model measured earlier (R5).

## P2. Averaged over instances, the product is right

**Proposition 2.** If o ~ N(0, σ²I\_d), then

  P(success) = ∏\_i erf(c\_i/(σ√2)) = E\_{r ~ σ²χ²\_d}[F\_B(r)].

**Proof.**
- The first equality: the coordinates of o in the orthonormal frame (u\_i) are i.i.d. N(0, σ²). This is the Lindner–Peikert formula.
- The second equality: write o = ‖o‖·(o/‖o‖). The norm and the direction are independent, ‖o‖² ~ σ²χ²\_d, and the direction is uniform. ∎

So the Lindner–Peikert / Gaussian product is exactly the **average over instances** of the exact law. The estimator's Π\_B(dσ²) matches it within 1% on the four bases checked (P2 table in `theory_check_log.txt`).

Together with P1:
- The estimator's per-attempt number is right **on average over instances**.
- For a single instance with error norm r, the correct number is F\_B(r), which is below Π\_B(r).
- The cancellation is between instances with small ‖e‖, which are easy, and instances with large ‖e‖, which are hard.

## P3. Repeated attempts are positively dependent, so amplify() undercounts

Let the instance's norm be r ~ μ. Let attempts j = 1..K succeed with probabilities F\_j(r), independently given r (Assumption A; the bases may differ).

**Proposition 3.**
- **(a)** P(attempts j and k both succeed) = E[F\_j F\_k] ≥ E[F\_j]·E[F\_k].
- **(b)** P(all K attempts fail) = E[∏\_j (1 − F\_j)] ≥ ∏\_j (1 − E[F\_j]).
  - Hence the number of attempts needed for 99% success is at least amplify(0.99, p̄) = log 0.01 / log(1 − p̄), where p̄ is the true mean per-attempt success.
  - The inequality is strict whenever F is not constant on the support of μ.
- **(c)** For identical bases (F\_j = F), the hazard h(k) = P(success at attempt k+1 | first k failed) = E[F(1−F)^k]/E[(1−F)^k] is non-increasing in k.
- **(d)** Suppose a fresh instance can be drawn after any failure, for example a fresh subset of LWE samples, which gives a fresh e. Then restarting after every failure minimises the expected attempts per solved instance, which equals 1/p̄. Retrying the same instance up to k times costs Σ\_{i<k} D(i)/(1 − D(k)) ≥ 1/p̄, where D(i) = E[(1−F)^i].

**Proof.**
- **(a), (b):** each F\_j is non-increasing in r and each 1 − F\_j is non-decreasing. Chebyshev's association inequality for comonotone functions of one variable gives (a). Applied inductively to products of non-negative non-decreasing functions, it gives (b).
- **(c):** h(k+1) ≤ h(k) is equivalent to E\_ν[F(1−F)] ≤ E\_ν[F]·E\_ν[1−F], i.e. Cov\_ν(F, 1−F) = −Var\_ν(F) ≤ 0, under the tilted measure ν ∝ (1−F)^k dμ.
- **(d):**
  - 1 − D(k) = Σ\_{i<k} (D(i) − D(i+1)) = Σ\_{i<k} D(i)·h(i).
  - By (c), h(i) ≤ h(0) = p̄, so 1 − D(k) ≤ p̄·Σ\_{i<k} D(i).
  - Rearranging gives Σ\_{i<k} D(i)/(1 − D(k)) ≥ 1/p̄, with equality at k = 1. ∎

**Check.** On the per-instance exact-law probabilities of the R8 and exploratory BKZ bases (`theory_check.py`, P3 section):
- P(all K fail) exceeds the independent value;
- the hazard is non-increasing;
- restarting after one failure is never worse.

`retry_cost.py` gives the measured versions.

## What this does and does not show

- **What it shows.** Under Assumption A, everything measured on BKZ bases follows from one fact: per-instance success is a decreasing function of ‖e‖, the same for every re-randomised basis. That one fact gives the dependence (R4), the success of the exact law (R8), the bias of the product (P1) and the fact that the average is right (P2).
- **What it does not show.**
  - Assumption A is an empirical statement. It is supported for BKZ (R8) and fails in part for LLL (R6, R9), where coordinates beyond the norm matter.
  - P1 and P3 hold for any basis profile. How large the effect is depends on the profile and on the spread of ‖e‖.
