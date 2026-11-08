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

Full record of the model tests, in order: R5 (product-over-levels fixed-norm model) **failed**; R6 (exact model, LLL and BKZ) **failed** on LLL; R7 (exact model, BKZ) **failed** on a degenerate setting; R8 (exact model, BKZ, with a degeneracy guard) **passed**; R9 (block-multiset law, LLL) **failed** narrowly (2 tail cells off, variance matched).

**Exploratory, LLL:** the extra dependence at LLL correlates with how ‖e‖ splits between the secret part s and the error part e (Spearman −0.37 against the residual). Re-randomisation only permutes coordinates within each block, so the pair (‖s‖, ‖e‖) is invariant, not just ‖o‖. A two-block law (fixed ‖s‖ and ‖e‖, random direction within each block, no fitted parameter) removes that correlation (−0.05) and raises the predicted count variance from 16.0 to 18.3, against 24.4 measured, at LLL n = 80, η = 2 on 4 lattices. The remaining dependence at LLL is still unexplained.

**What this shows:**
1. **Repeated decoding attempts on one LWE instance are dependent.** This held in all 8 settings, 4 of them held out.
2. **For BKZ-reduced bases the dependence is explained, with no fitted parameter, by the instance's error norm.** The exact fixed-norm law predicts the whole "solved within k attempts" curve and the never-solved share on held-out settings; the estimator's independent model does not.
3. **For LLL-reduced bases there is further dependence beyond ‖e‖, so attempts are even more correlated.** Its cause is open.
4. **The estimator's prob.babai is right on average by cancellation, not by design.** At a fixed error norm it is biased upward.

The literature check now includes the full texts of 2025/2195 and Nearest Planes in Practice, plus a full-text search of Wunderer 2019. Wunderer states the property tested here as an assumption ("p(v) is equal to some constant probability p … for all v ∈ S", Assumption 1) and charges repetitions as T_hyb/p_succ. Neither he nor de Perthuis–Trenkić measures it for decoding. Liu–Nguyen 2013 is paywalled and was not read. Details are in `research_notes/novelty_check_phase2.md`.

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

They neither measure nor model per-instance dependence, so the claim below stands.

## What is new, and what isn't

- **New, to the extent checked:** a direct measurement showing that re-randomized decoding attempts on one LWE instance are significantly dependent, with the dependence tied to ‖e‖. As a result, the estimator's independent-trials amplification overstates multi-attempt success; at one setting the share of instances never solved is 25× the model's prediction.
- **Not new:** the idea of fixing the vector's length and integrating over it; that is 2025/2195's, for uSVP.
- **Also new, confirmed by a test fixed in advance (R8) on fresh instances:** for BKZ-reduced bases, conditioning on each instance's own error norm, through the exact joint fixed-norm law, accounts for all of the dependence between repeated attempts; the estimator's constant-p model does not (off in 12 of 16 cells). The fixed-norm computation itself follows the Gama–Nguyen–Regev style of analysis and is not claimed as new. What is new is measuring it against repeated decoding and showing that it is the missing ingredient in the lattice estimator's repetition model. This also explains why the estimator's per-level formula is right on average but biased for any fixed instance.
- **Not shown:**
  - A model for LLL-reduced bases.
  - Any change to a published security estimate.
- **Literature check:**
  - Full texts read: 2025/2195, "Nearest Planes in Practice", Luan et al. 2023 and Liu–Nguyen 2013.
  - Searched in full text: Wunderer 2019.
  - Not read: Wunderer's 2018 thesis and Kirshanova–May–Wiemer 2016.

**Next, if pursued:**
1. Find out why the norm-conditioned sphere formula is about 10% too optimistic per attempt.
2. Test whether residual dependence beyond ‖e‖ (lattice-level) explains the remaining 26% of the excess variance at LLL η=2.
3. Check the GPU hybrid attack paper (ePrint 2025/1990) for the same pattern in its predicted versus observed success rates.

Files: `retry_study.py` (rules and code), `retry_study_results.json`, `retry_study_log.txt`, `retry_impact.py`.
