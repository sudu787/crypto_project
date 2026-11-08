# Are repeated decoding attempts on one LWE instance independent? (7 Nov 2026)

**Question.** The lattice estimator charges repeated Babai attempts as independent trials: amplify(0.99, p) = log(0.01)/log(1 − p) (`PrimalHybrid`, "Repeat whole experiment ~1/prob times"). On a single LWE instance the error vector is fixed, so the attempts may not be independent. de Perthuis–Trenkić (PQCrypto 2026, ePrint 2025/2195) make the analogous point for the uSVP route; this tests it for the decoding step.

**Setup** (toy parameters only; nothing here is a statement about ML-KEM's security):
- q = 3329, m = n, CBD η ∈ {2, 3}.
- 16 lattices × 200 targets per setting.
- Re-randomisation: each attempt permutes the samples and the secret coordinates, which gives an isometric copy of the same instance with the same ‖e‖. The basis is reduced from scratch: LLL at n = 80 (256 attempts per instance), and fplll BKZ-20 at n = 100 (64 attempts per instance).
- 5,120 bases in total.
- Success comes from the exact Babai identity, checked against the GPU decoder on 3,200 decodes.
- The rules were fixed before the run, in the docstring of `retry_study.py`.

## Results

**R4: independence is rejected in all 4 settings** (permutation test, p ≤ 4·10⁻⁴).

| Setting | Success per attempt | Variance of success counts: measured / independent model / fixed-error model | Spearman(‖e‖, count) |
|---|---|---|---|
| LLL n=80 η=2 | 2.4% | 23.2 / 6.1 / 18.8 | −0.62 |
| LLL n=80 η=3 | 0.22% | 0.93 / 0.57 / 1.05 | −0.39 |
| BKZ-20 n=100 η=2 | 3.9% | 3.71 / 2.45 / 4.17 | −0.55 |
| BKZ-20 n=100 η=3 | 0.31% | 0.22 / 0.20 / 0.29 | −0.26 |

The independent model overstates multi-attempt success, which is the direction that makes attacks look cheaper:

| Setting | Attempts | Independent model | Measured (99% interval) | Never solved: predicted vs measured |
|---|---|---|---|---|
| LLL n=80 η=2 | 128 | 95.4% | 85.8% (84.1–87.3) | 0.2% vs 5.0% |
| LLL n=80 η=3 | 256 | 43.5% | 35.4% (33.2–37.6) | 56.5% vs 64.6% |
| BKZ-20 n=100 η=2 | 64 | 92.6% | 87.1% (85.5–88.5) | 7.4% vs 12.9% |
| BKZ-20 n=100 η=3 | 64 | 18.4% | 17.4% (15.8–19.2) | 81.6% vs 82.6% (inside) |

At LLL η=2 the independent model's single-attempt rate is right: it predicts 54.1% within 32 attempts, consistent with p = 2.4%. The gap at many attempts therefore comes from the dependence. Reaching 95% takes 256 attempts against the model's roughly 123.

**R5: the proposed fixed-error model fails.** It is off in 16 of 16 cells, against 10 for the independent model. The model fixes ‖e‖ per instance and integrates over its distribution. It captures most of the dependence: at LLL η=2 it accounts for 74% of the excess variance, and it slightly overshoots the variance in the other three settings. But the sphere formula averaged over ‖e‖ overstates per-attempt success by about 10% relative, and that compounds over many attempts. The dependence is real; this particular model is not accurate enough.

## Follow-up: the exact fixed-norm model (`retry_exact.py`)

**Why R5 failed.** The estimator's prob.babai multiplies per-level probabilities. For a vector of *fixed* length the levels are negatively dependent: a small projection on one direction forces larger ones elsewhere. So the per-level product is too optimistic at a fixed ‖e‖. The exact fixed-norm law has no free parameters: P(success | ‖o‖ = r) = P(r < min_i (‖b*_i‖/2) / |z_i|) for z uniform on the unit sphere, computed with 200,000 directions per basis on the GPU.

On every setting it gets the per-attempt mean right. The product formula is about 10–15% too high at the true ‖e‖; evaluated at the mean radius √d·σ, as the estimator does, the two errors happen to cancel.

| Setting | Per attempt, measured | Exact model | Product, fixed norm | Independent (estimator) |
|---|---|---|---|---|
| LLL n=80 η=2 | 2.39% | 2.36% | 2.74% | 2.42% |
| BKZ-20 n=100 η=2 | 3.86% | 3.85% | 4.34% | 3.98% |
| LLL n=76 η=3 (held out) | 1.86% | 1.85% | 2.19% | 1.92% |
| BKZ-10 n=90 η=2 (held out) | 9.36% | 9.19% | 10.01% | 9.37% |

**Rule R6** was fixed before the held-out bases were reduced: LLL n = 76 and BKZ-10 n = 90 on fresh instances, 5,120 new bases. It required the exact model to be off in at most 2 of 16 cells and to match the count variance within 25% everywhere. **R6 failed:** the exact model was off in 8 cells, against 13 for the independent model, and the variance missed at LLL.

The failure comes entirely from LLL. Split by reduction type, which was not part of the rule and is stated here as a post-hoc split:

| Bases | Cells off: exact / independent | Count variance: measured / exact / independent |
|---|---|---|
| BKZ-20 n=100, η=2 and η=3 (exploratory) | 0 / 4 of 8 | 3.71 / 3.70 / 2.45 and 0.218 / 0.220 / 0.202 |
| **BKZ-10 n=90, η=2 and η=3 (held out)** | **0 / 5 of 8** | 11.58 / 10.58 / 5.44 and 0.98 / 0.96 / 0.76 |
| LLL n=80 and n=76 (both) | 13 / 15 of 16 | e.g. 185 / 126 / 25 at n=76 η=2 |

**Rule R7, a confirmation run for BKZ only** (fixed before its bases were reduced: BKZ-15 n = 90 and BKZ-20 n = 110 on fresh instances, 2,048 bases; same cells and criteria as R6):
- The exact model was off in **0 of 16 cells**; the independent model was off in 5.
- The variance criterion **failed**, so **R7 failed**. The cause is BKZ-20 n = 110, which I chose too hard: 0.01% success per attempt at η = 2 and no successes at all at η = 3. There the variance ratio is meaningless (η = 2) or undefined (η = 3), and the rule had no guard against that.
- At BKZ-15 n = 90 the predicted count variance was within 3% of the measured one (29.74 vs 30.60 at η = 2, 6.745 vs 6.710 at η = 3), and every cell was inside its interval.

**Rule R8** (fixed 8 Nov, before its bases were reduced) repeats R7 on BKZ-20 n = 95 and BKZ-10 n = 85 on fresh instances. Its degeneracy guard was written in advance: a (setting, η) with fewer than 50 successes in total is excluded from the variance criterion, and more than one such case fails the test.

**R8 passed.** On 2,048 fresh bases (16 lattices × 200 targets × 64 attempts per setting), the exact fixed-norm model was off in **0 of 16** cells; the estimator's independent model was off in **12 of 16**. No setting was degenerate (7,530 to 68,843 successes each). The predicted count variance was within 2.7–6.3% of the measured one in all four:

| Fresh setting | Per attempt | Count variance: measured / exact / independent | Never solved in 64: measured / exact / independent |
|---|---|---|---|
| BKZ-20 n=95 η=2 | 19.6% | 23.19 / 22.56 / 10.06 | 0.0% / 0.0% / 0.0% |
| BKZ-20 n=95 η=3 | 3.7% | 3.94 / 3.69 / 2.25 | 16.3% / 15.8% / 9.2% |
| BKZ-10 n=85 η=2 | 33.6% | 39.79 / 38.14 / 14.41 | 0.0% / 0.0% / 0.0% |
| BKZ-10 n=85 η=3 | 9.5% | 12.39 / 11.79 / 5.55 | 1.2% / 1.4% / 0.2% |

**Bias of the per-level formula (test run after the data was in, from the runs above).** The estimator's per-level product, evaluated at each instance's true ‖e‖, overstates the measured per-attempt success in **14 of 14** non-degenerate settings, by +4% to +33% (one-sided sign test p = 6·10⁻⁵; counting each lattice setting once, because the η = 2 and η = 3 runs share bases, 7 of 7, p = 0.008). The exact joint law is within about 2% of the measurement in every setting. Evaluated at the mean radius √d·σ, as the estimator does, the product lands within 0–3.5% of the measurement: the upward bias and the spread of ‖e‖ cancel on average.

**LLL: the block-multiset law (rule R9, fixed before its bases were reduced).** Re-randomisation permutes coordinates only within the secret block and within the sample block, so each block's coordinate multiset is exactly what stays fixed. The block-multiset law takes, for each basis, the success share over random within-block permutations of the instance's own offset; it has no free parameters. On 2,048 fresh LLL bases (n = 78, 128 attempts per instance):

| Fresh LLL n=78 | Count variance: measured / multiset / exact fixed-norm / independent | Cells off: multiset / exact / independent |
|---|---|---|
| η=2 | 20.30 / 19.72 / 15.09 / 6.69 | 2 / 4 / 4 |
| η=3 | 1.317 / 1.385 / 1.214 / 0.891 | 0 / 2 / 3 |

**R9 failed narrowly.** It was off in 2 cells, where the rule allowed 1: the far tail at η = 2, with 3.5% never solved in 128 attempts against 2.7% predicted. The variance criterion passed (within 3% and 5%). So at LLL quality almost all of the dependence comes from the instance's own coordinates, and a small excess in the never-solved tail remains unexplained.

Full record of the model tests, in order: R5 (product-over-levels fixed-norm model) **failed**; R6 (exact model, LLL and BKZ) **failed** on LLL; R7 (exact model, BKZ) **failed** on a degenerate setting; R8 (exact model, BKZ, with a degeneracy guard) **passed**; R9 (block-multiset law, LLL) **failed** narrowly (2 tail cells off, variance matched); R10 (scale-up: Babai n = 120, enumeration n = 150, BKZ-40) **passed**; R11 (block-multiset law, scrambled LLL) **passed**; R12 (fixed-norm law, pruned enumeration) **passed**; R13 (exact law, TU Darmstadt challenge instances) **passed**.

**Exploratory, LLL:** the extra dependence at LLL correlates with how ‖e‖ splits between the secret part s and the error part e (Spearman −0.37 against the residual). Re-randomisation only permutes coordinates within each block, so the pair (‖s‖, ‖e‖) is invariant, not just ‖o‖. A two-block law (fixed ‖s‖ and ‖e‖, random direction within each block, no fitted parameter) removes that correlation (−0.05) and raises the predicted count variance from 16.0 to 18.3, against 24.4 measured, at LLL n = 80, η = 2 on 4 lattices. The remaining dependence at LLL is still unexplained.

## Follow-up 2 (8 Nov): theory, cost, LLL, enumeration, estimator patch, scale, real challenge data

### Theory (`Retry_theory.md`, checked by `theory_check.py`, log `theory_check_log.txt`)
Three short results, each with a proof and a numerical check on real bases:
- **P1. For one instance, the per-level product is biased upward.** At a fixed error norm, the exact law is at most the per-level product. Fixing the norm makes the levels negatively dependent; the proof conditions on one coordinate at a time.
  - 0 violations on 4 bases × 33 radii.
  - Π/F = 1.004–1.29, which explains the bias found by the sign test.
- **P2. Averaged over instances, the product is right.** For Gaussian error, the Lindner–Peikert erf product equals the exact law averaged over ‖e‖ (E_r F(r)).
  - On all 4 bases the two match to 0.001.
  - The estimator's Π(dσ²) is within 1% of both.
- **P3. Repeated attempts are positively dependent, so amplify() undercounts.**
  - P(all K fail) ≥ ∏(1 − p̄), so the attempts needed for 99% are at least amplify(0.99, p̄).
  - The chance that the next attempt succeeds, after k failures, never increases.
  - If a fresh instance is available, restarting after every failure is optimal.

### Item 2. What the dependence costs (`retry_cost.py`, `retry_cost_log.txt`; R8 and exploratory BKZ bases)
The exact model reproduces the measured "solved within k" curve and the per-attempt success after k failures, up to k = 64 (log). Attempts needed for 99% of instances:

| Setting | p per attempt | amplify(0.99, p) | Exact model | Ratio |
|---|---|---|---|---|
| BKZ-10 n=85 η=2 | 33.6% | 11.2 | 14 | 1.25 |
| BKZ-20 n=95 η=2 | 19.6% | 21.1 | 27 | 1.28 |
| BKZ-10 n=85 η=3 | 9.5% | 45.9 | 71 | 1.55 |
| BKZ-20 n=100 η=2 | 3.9% | 116.9 | 189 | 1.62 |
| BKZ-20 n=95 η=3 | 3.7% | 122.9 | 222 | 1.81 |
| BKZ-20 n=100 η=3 | 0.31% | 1,467 | 4,097 | 2.79 |

**Give-up rule.** Suppose fresh instances are available, for example a fresh subset of LWE samples, which gives a fresh e. Then abandoning an instance after one failed attempt minimises the attempts per solved instance, which equals 1/p̄. Retrying the same instance indefinitely costs 1.0–1.44× more:
- 469 attempts instead of 325 at BKZ-20 n=100 η=3;
- 36.2 instead of 27.7 at BKZ-20 n=95 η=3.

The measured curves agree, up to k = 64.

### Item 4. Why LLL differs, and a confirmed fix (`retry_lll.py`, rule R11)
Exploratory, from basis geometry only (no decoding outcomes):
- **The secret block carries more weight.** LLL's last Gram–Schmidt directions put 69% of their mass on the secret block, against 59% for BKZ-10 and 56% for BKZ-20. So on LLL bases, success depends on ‖s‖ and ‖e‖ separately. This is why the norm-only law failed (R6) and the block-aware law did better (R9).
- **Same-lattice LLL bases are slightly more aligned** than bases of different lattices: ratio 1.07, against 1.04 for BKZ-10 and 1.00 for BKZ-20. My first comparison, against random subspaces, suggested 1.8×. That was mostly the block concentration above, not lattice-specific alignment.
- **No q-vector Z-shape** appears in any basis checked.

**R11** (fixed before its bases were reduced) adds scrambling: a random unimodular transform before LLL, as in GNR extreme pruning. It then reruns R9's test on 2,048 fresh LLL n=78 bases.

**R11 passed.** The block-multiset law was off in **0 of 8** cells, against 7 for the independent model and 3 for the exact fixed-norm law. Its variance was within 2% (η=2: 18.49 vs 18.24 measured) and within 1% (η=3: 1.341 vs 1.331).

So the R9 tail miss came from permutation-only re-randomisation. With scrambled LLL, the dependence is fully explained by the instance's own coordinates.

### Item 8. Pruned enumeration (`retry_enum.py`, rule R12)
Attempt: BDD enumeration with GNR linear pruning, R² = 1.1·d·σ², on the R8 bases. The radius was chosen from the model alone, for about 16% success per attempt. Success holds iff every projection of o onto the last k Gram–Schmidt directions has squared norm ≤ (k/d)R² (Liu–Nguyen Alg. 4).

Under the fixed-norm model, this success probability doesn't depend on the basis at all, only on ‖o‖²/R². So retrying can only help through the random direction.

**R12 passed** (fixed before any enumeration outcome was computed):
- Independence was rejected in all 4 settings (p < 10⁻⁴).
- The fixed-norm law was off in **0 of 16** cells; the independent model ("success multiplied by ℓ", Liu–Nguyen §3.5), with the *correct* mean, was off in **16 of 16**.

| Setting | p per attempt | Count variance: measured / fixed-norm / independent | Never solved in 64: measured / fixed-norm / independent |
|---|---|---|---|
| BKZ-20 n=95 η=2 | 15.9% | 58.6 / 56.9 / 8.5 | 14.0% / 14.1% / 0.0% |
| BKZ-20 n=95 η=3 | 15.8% | 63.2 / 61.9 / 8.5 | 16.4% / 16.3% / 0.0% |
| BKZ-10 n=85 η=2 | 15.5% | 63.0 / 63.1 / 8.5 | 16.7% / 16.6% / 0.0% |
| BKZ-10 n=85 η=3 | 15.8% | 68.9 / 65.7 / 8.5 | 18.5% / 18.5% / 0.0% |

For pruned enumeration, the effect is much larger than for Babai. About one instance in six can never be solved by re-randomising the basis, whatever the number of attempts. The independent model says none are left after 64.

### Item 5. Lattice estimator patch (`estimator_fixed_error.patch`, `retry_impact2.py`, `retry_impact2_log.txt`)
The patch is on a local branch of malb/lattice-estimator (base commit d857637) and has not been submitted anywhere. It changes two things:
- **New function:** `prob.amplify_fixed_error(target, r, stddev, other_probability)`. It returns the attempts k with E over ‖e‖² ~ σ²χ²_d of (1 − other·babai(r, ‖e‖))^k = 1 − target.
- **New option:** `repetition_model="fixed_error"` for `primal_hybrid`. The default `"independent"` is unchanged and gives bit-identical outputs.
- **Lower bound:** by P1 the result is a lower bound on the fixed-norm attempts, so it stays conservative for security estimates.
- **Tests:** all 15 doctests pass, including a new one.

Results, with the optimiser re-run under each model:
- **Babai hybrid without MitM:**
  - Kyber512 +4.99 bits (2^221.9 → 2^226.9).
  - HES ternary +1.65.
  - TFHE630 +1.02, Concrete_TFHE586 +1.18, TFHE1024 +0.65.
  - SEAL20 +0.17, and ≤ 0.05 for HElib and CHHS.
  - The smaller Babai's per-attempt probability, the larger the shift.
- **With MitM:**
  - Kyber512 +1.73, HES ternary +0.15, and ≤ 0.01 elsewhere.
  - In most of these sets, Babai's per-attempt probability is near 1 and the failures come from guessing.
  - The MitM success probability also depends on σ; it is kept norm-independent here, which is a limitation.
- **No best-primal estimate moves:** where the shift is largest, uSVP/BDD is cheaper than the hybrid.

### Item 7. Real challenge instances (`lwe_challenge.py`, rule R13; `lwe_challenge_analyse_log.txt`)
**Data.** Public TU Darmstadt LWE challenge files: uniform secret, Gaussian error σ = αq, q ≈ n².
- Each file's samples are split into disjoint blocks; each block is one instance with its own e.
- Attempts permute the block's samples and reduce with BKZ.
- The secret is not published. Real Babai found it for both files used, and the residual over all samples matched the expected Gaussian size (327 vs 320 for n = 40; 463 vs 456 for n = 45).
- The projection identity agreed with real Babai on all 143 checks.
- Only n = 40 and n = 45 at α = 0.005 had usable success rates on this machine; every α ≥ 0.010 file, and n ≥ 50, was ≈ 0 for BKZ ≤ 30.

**R13 passed** (fixed before its bases were reduced). Pearson X² of per-instance success counts over 24 instances, 64 attempts each:
- exact law: 33.4, p = 0.095;
- independent model: 62.5, p = 3·10⁻⁵.

The evidence comes almost entirely from **n = 40** (BKZ-20, 17% per attempt):
- independence was rejected, p ≈ 10⁻⁴;
- X² was 16.8 for the exact law against 46.3 for the independent model, on 13 instances;
- the instance with ‖e‖² at 0.88 of the mean was solved 22 times out of 64; the one at 1.27 was solved 6 times; the independent model predicts about 13 for both.

At **n = 45** (BKZ-30, 5% per attempt) the counts are too small to separate the models: X² 16.7 against 16.2, and the independence test gives p = 0.12.

### Item 1. Scale-up (`retry_scale.py`, rule R10; `retry_scale_test_log.txt`)
R10 was fixed before its bases were reduced. It used 1,536 fresh BKZ-40 bases (16 lattices each):
- **(a)** Babai at n = 120, with R8's rule (64 attempts per instance).
- **(b)** Pruned enumeration at n = 150, with R12's rule (32 attempts per instance).

Babai at n ≥ 150 was ≈ 0 in the probes even with BKZ-50, so it could not be tested there.

**R10 passed.**
- **(a) Babai, n = 120:** the exact law was off in **0 of 8** cells; the independent model was off in 4. The count variance was 17.6 measured, 17.6 exact and 10.6 independent at η=1 (20.6% per attempt). It was 0.55 / 0.53 / 0.48 at η=2 (0.75% per attempt), where 65.2% of instances were never solved in 64, against 64.3% predicted.
- **(b) Enumeration, n = 150:** independence was rejected at both η (p < 10⁻⁴). The fixed-norm law was off in **0 of 8** cells and the independent model in 7. The never-solved share in 32 attempts was 10.1% / 13.6% measured, 9.5% / 13.8% fixed-norm and 0.6% independent.

### Robustness check (post hoc; `retry_calibration.py`, `retry_bkz10_multiset.py` and their logs)
Two weaknesses of the cell tests above were checked on the saved R8 and exploratory BKZ data (16 lattices × 200 instances × 64 attempts):
- **Shared lattices.** All 200 instances of a lattice are decoded on the same bases, so the Wilson intervals were too narrow. Every interval here is a lattice-level bootstrap.
- **Aggregate cells.** The cells test pooled shares. Here each instance is tested on its own: a model gives the instance a success probability per attempt, its count is then Poisson-binomial, and the randomised PIT is uniform, with variance 1/12 = 0.0833, if the model is right. A variance above that means the model predicts too little spread.

The comparison is against a "pooled" model: independent trials with the same mean per lattice and attempt.

| Setting | Never solved in 64: measured / exact / pooled | PIT variance: exact / pooled (95% CI excludes 0.0833?) |
|---|---|---|
| BKZ-20 n=95 η=3 | 16.3% / 15.8% / 9.5% | 0.086 ok / 0.104 off |
| BKZ-20 n=95 η=2 | 0.03% / 0.01% / 0.00% | 0.085 ok / 0.123 off |
| BKZ-20 n=100 η=2 | 12.9% / 13.3% / 8.1% | 0.083 ok / 0.102 off |
| BKZ-20 n=100 η=3 | 82.6% / 83.0% / 82.1% | 0.084 ok / 0.084 ok |
| BKZ-10 n=85 η=2 | 0.0% / 0.0% / 0.0% | **0.091 off** / 0.132 off |
| BKZ-10 n=85 η=3 | 1.25% / 1.37% / 0.18% | **0.090 off** / 0.120 off |

- **Strengthened:** with lattice-level intervals, the exact law matches the never-solved share in all 6 settings, while the pooled model misses it in 3. At BKZ-20 the exact law passes the per-instance test as well.
- **Weakened:** at BKZ-10 n=85 the exact law leaves a small, significant residual. It explains about 85% of the excess spread, not all of it. The R8 cell test was too coarse to see this.
- **Block-multiset law at BKZ-10** (the law that fixed LLL): the PIT variance drops to 0.087 (η=2) and 0.088 (η=3), still outside the interval. So the secret-block weighting accounts for about half of the residual. About 8–12% of the excess spread at BKZ-10 remains unexplained, presumably the same-lattice alignment seen for LLL (ratio 1.04 at BKZ-10).

**Threats to validity.**
- **Order of the models.** The exact law was adopted after R5 failed, and R8 after R6 and R7 failed. Each later test was fixed before its own bases were reduced, on fresh instances. But the sequence R5→R8 is itself a search over models, and that should be said when this is published.
- **Interpretation.** R10–R13 were all fixed in advance and all passed, which limits the concern. This check, however, is post hoc.

### Item 3. Remaining literature
- **Kirshanova–May–Wiemer 2016** (ePrint 2016/380, read): they explicitly do not use re-randomise-and-repeat ("We do not consider the so-called Extreme Pruning strategy … re-randomizing an instance causes re-running the expensive BKZ reduction"). It has no retry success model.
- **Wunderer's 2018 thesis:** not read. The file supplied (`thesis_published.pdf`) is a different TU Darmstadt thesis (J. Brendel, *Future-Proofing Key Exchange Protocols*, 2019).

**What this shows:**
1. **Repeated decoding attempts on one LWE instance are dependent.** This held in all 8 settings, 4 of them held out.
2. **For BKZ-reduced bases the dependence is explained, with no fitted parameter, by the instance's error norm.** The exact fixed-norm law predicts the whole "solved within k attempts" curve and the never-solved share on held-out settings; the estimator's independent model does not. At BKZ-20 this holds even instance by instance; at BKZ-10 a small residual remains (about 8–12% of the excess spread; see the robustness check).
3. **For LLL-reduced bases there is further dependence beyond ‖e‖, so attempts are even more correlated.** It comes from LLL's weighting toward the secret block (success depends on ‖s‖ and ‖e‖ separately) plus a small same-lattice alignment under permutation-only re-randomisation. With scrambled re-randomisation, the block-multiset law explains it (R11, passed).
4. **The estimator's prob.babai is right on average over instances, and biased upward for any one instance.** P1 and P2 prove both.
5. **The same holds, more strongly, for pruned enumeration** (R12, passed): about one instance in six is never solved by re-randomising.

The literature check now includes the full texts of 2025/2195 and Nearest Planes in Practice, plus a full-text search of Wunderer 2019. Wunderer states the property tested here as an assumption ("p(v) is equal to some constant probability p … for all v ∈ S", Assumption 1) and charges repetitions as T_hyb/p_succ. Neither he nor de Perthuis–Trenkić measures it for decoding. Liu–Nguyen 2013 was read first-hand (see Prior work checked). Details are in `research_notes/novelty_check_phase2.md`.

## Impact on real estimates (lattice estimator, exploratory, `retry_impact.py`)

The estimator's model was re-run with the error fixed per instance:
- **Where the Babai hybrid is the best attack** (CHHS_1024_25 at 2^112.6, HElib120_1024 at 2^83.1), the optimizer already sits at a per-attempt Babai probability of 0.3–0.6. Failures there come from guessing, and the correction is ≤ 1.03×.
- **Where Babai's p is small** (TFHE630, Concrete_TFHE586, TFHErs_LWE, HES ternary), repetitions grow 2–3×, adding 1–1.7 bits. In those cases the hybrid is not the best attack, so no headline estimate moves.
- **For Kyber**, the best primal attack does not repeat Babai at all.

## Prior work checked

Read in full: de Perthuis–Trenkić 2025 (uSVP only; fixes the analogous assumption there), Bischof et al. "Nearest Planes in Practice" (runtime only), Luan et al. 2023 (open access). Searched in full text: Wunderer 2019. Also checked: the lattice estimator's code. According to Luan et al., Liu–Nguyen 2013 adopt the Lindner–Peikert Gaussian success probability. Every one of these uses a single averaged per-attempt success probability with independent repetitions over re-randomised bases. None measures or models the per-instance dependence. **Liu–Nguyen 2013, read first-hand (8 Nov 2026, LNCS 7779 pp. 293–309):**
- Sec. 3.5 states that with ℓ randomized bases "the success probability is also heuristically multiplied by ℓ". That is the independence assumption, used without a test.
- Sec. 4.1–4.2 use GNR's error-uniform-on-a-sphere model, with R set to the *expected* error length. They call this "a rough estimate", sample the error distribution instead, and use the fixed-norm law only as a lower bound. They never condition on each instance's own ‖e‖.
- In the GGH experiments they reduce one basis and say all keys could be recovered "simply by repeating our experiments a small number of times". That claim is not tested.

They neither measure nor model per-instance dependence, so the claim below stands. Kirshanova–May–Wiemer 2016 (read) leave re-randomise-and-repeat out entirely.

## What is new, and what isn't

- **New, to the extent checked:** a direct measurement showing that re-randomized decoding attempts on one LWE instance are significantly dependent, with the dependence tied to ‖e‖. As a result, the estimator's independent-trials amplification overstates multi-attempt success; at one setting the share of instances never solved is 25× the model's prediction.
- **Not new:** the idea of fixing the vector's length and integrating over it; that is 2025/2195's, for uSVP.
- **Also new, confirmed by a test fixed in advance (R8) on fresh instances:** for BKZ-reduced bases, conditioning on each instance's own error norm, through the exact joint fixed-norm law, accounts for the dependence between repeated attempts in every cell test; the estimator's constant-p model does not (off in 12 of 16 cells). A stricter per-instance test (post hoc) confirms this at BKZ-20 and finds a small residual at BKZ-10. The fixed-norm computation itself follows the Gama–Nguyen–Regev style of analysis and is not claimed as new. What is new is measuring it against repeated decoding and showing that it is the missing ingredient in the lattice estimator's repetition model. This also explains why the estimator's per-level formula is right on average but biased for any fixed instance.
- **Also new (8 Nov follow-up):**
  - Proofs that the per-level product is biased upward per instance and right on average (P1, P2), and that amplify() undercounts (P3).
  - The same dependence for pruned enumeration (R12).
  - The LLL mechanism, with a passed test (R11).
  - A tested estimator option.
  - The results hold at BKZ-40, Babai n = 120 and enumeration n = 150 (R10), and on real TU Darmstadt challenge instances (R13).
- **Not shown:**
  - Any change to a published *best* attack estimate.
  - Results beyond n = 120 for Babai (success is ≈ 0 there on this hardware); n = 150 is covered only for enumeration (R10, passed).
- **Literature check:**
  - Full texts read: 2025/2195, "Nearest Planes in Practice", Luan et al. 2023, Liu–Nguyen 2013 and Kirshanova–May–Wiemer 2016.
  - Searched in full text: Wunderer 2019.
  - Not read: Wunderer's 2018 thesis, because the wrong file was supplied.

**Next, if pursued:**
1. Read Wunderer's 2018 thesis.
2. Check the GPU hybrid attack paper (ePrint 2025/1990) for the same pattern in its predicted versus observed success rates.
3. Model the MitM step's dependence on σ in the estimator patch.
4. Explain the BKZ-10 residual. Rerun BKZ-10 with scrambled re-randomisation, as in R11: if the residual disappears, it was same-lattice alignment. Fix the per-instance PIT test in advance as the criterion.
5. Use the per-instance PIT test with lattice-level intervals as the criterion in future pre-registered rules, rather than pooled cells.

Files: `retry_study.py` (rules and code), `retry_study_results.json`, `retry_study_log.txt`, `retry_impact.py`.
