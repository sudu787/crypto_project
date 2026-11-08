# Decoding-step study: summary (7 Nov 2026)

**Question.** In the primal attack on LWE, the last step decodes a target against a reduced basis (Babai or Lindner-Peikert). Attack-cost tools such as the lattice estimator predict how often that step succeeds. How accurate is that prediction? And does using ML-KEM's exact centred-binomial (CBD) error, in the model or when picking the final candidate, improve anything?

**Setup.** Toy parameters only: q = 3329, n = 70-100, lattice dimension 2n, CBD η = 2 and 3. LLL, BKZ-10 and BKZ-20 bases from fplll. 9 (reduction, n) settings × 2 η, 16 lattices × 100 targets each, so 1,600 targets per setting. The estimator was run at its current commit under SageMath. Rules for calling a result off or significant were fixed before any run. Every quoted number is asserted in the notebook `BDD_decoding_study.ipynb`.

## Results

1. **The estimator's Babai prediction is off at 17 of 18 settings, mainly because our BKZ bases were not fully reduced.** At BKZ-20, n = 100, η = 2 it predicts 54% where 4% succeed. Our bases came from fplll BKZ with auto-abort, at most 16 tours. A convergence test (`converge_test.py`) ran 100–200 more tours, which brought δ from 1.0175 to 1.0136 for BKZ-20 at n = 100. That is at or better than the estimator's 1.0142, so the estimator's assumption is right for converged BKZ. For LLL it is too pessimistic (35% vs 44%), because of the profile's tail; this was not looked into further.
2. **The estimator's formula is accurate on the real basis.** It falls inside the interval at all 18 settings. The Gaussian-vs-CBD error law contributes at most 0.4 points and independence across levels at most 0.3. This is expected, not new.
3. **The exact CBD error changes nothing at these sizes (null).** The Gaussian and CBD models agree within 0.7 points everywhere, for Babai and for Lindner-Peikert. The Gram-Schmidt directions mix many coordinates, so the projected CBD error is effectively Gaussian.
4. **A CBD prior or ±η box cannot improve the final pick (null).** On all 28,800 Lindner-Peikert decodings, whenever the true point was among the candidates it was also the shortest. Failures come from not generating the true point, never from ranking it wrongly.

## What is new and what isn't

- **Not contributions:** VA-ANP (shown earlier), the CBD-exact decoding model, and CBD-aware candidate selection. The last two are measured nulls.
- **The earlier "possible contribution" is withdrawn.** The estimator's error came mostly from our under-reduced bases. This study has no novel contribution.

## Limits

Toy sizes only, with BKZ block size at most 20, so this says nothing about ML-KEM security. The 1,600 targets share 16 lattices, so the intervals are somewhat optimistic. BKZ-15/25, larger n, pruned enumeration and the hybrid attack's meet-in-the-middle step were not done.

## Next step

A fair test of the estimator needs the bases rebuilt with BKZ run to convergence. That would validate the estimator; it would not give a new method. A paper aimed at Africacrypt (15 Jan 2027) needs a different idea.
