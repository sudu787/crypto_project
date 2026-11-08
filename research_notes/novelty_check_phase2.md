# Novelty check, phase 2 (7 Nov 2026)

Question: has anyone validated the lattice estimator's Babai / Lindner-Peikert success prediction against measured decoding on reduced q-ary bases at small block sizes, or attributed its error to the basis-profile model?

## Read (abstract pages, in the browser)
- de Perthuis, Trenkić. Refined Modelling of the Primal Attack… PQCrypto 2026, [ePrint 2025/2195](https://eprint.iacr.org/2025/2195). Abstract: refines the uSVP-route estimators (DDGR20, PV21); fixes the short vector's length and uses the full error distribution, not only two moments. No mention of Babai/BDD decoding. A search excerpt suggested a GSA-based prediction overestimating success in small-block experiments (Sec. 3.3, Fig. 4); that is about the uSVP route, but the full text was not readable to confirm.
- Albrecht, Li. Predicting BKZ Z-Shapes on q-ary Lattices, [ePrint 2022/843](https://eprint.iacr.org/2022/843), withdrawn 2022-08-09 (no reason given). Simulator for the q-ary Z-shape; consequence stated for enumeration-based primal cost. No mention of decoding success.
- Song et al. PS-BKZ, [ePrint 2026/2736](https://eprint.iacr.org/2026/2736). BKZ variant speed/quality on q-ary bases. Not about decoding prediction.

## Search results only (not read)
- Zhao, Xu. On the Measurement and Simulation of the BKZ Behavior for q-ary Lattices, Inscrypt 2022 ([Springer](https://link.springer.com/chapter/10.1007/978-3-031-26553-2_25)). Simulator for q-ary profiles where the Z-shape disappears.
- Postlethwaite, Virdia. On the Success Probability of Solving Unique SVP via BKZ, [ePrint 2020/1308](https://eprint.iacr.org/2020/1308.pdf). uSVP, not decoding.
- Nearest Planes in Practice (TU Darmstadt, [PDF](https://download.hrz.tu-darmstadt.de/media/FB20/Dekanat/Publikationen/Crossing/Nearest_Planes_in_Practice.pdf)); a search excerpt says the product-erf formula is an accurate approximation for wide discrete Gaussian error. That matches our finding that the formula is accurate on the real basis; it may also contain profile comparisons. **Not read; highest priority to check.**
- Wunderer, J. Math. Cryptology 2019, and Wunderer 2016 ([ePrint 2016/733](https://eprint.iacr.org/2016/733.pdf)). Source of the estimator's model; experiments not checked.

## Not readable
The ePrint PDFs sit behind a Cloudflare check and Springer behind a login. Getting the full texts of 2025/2195, Zhao-Xu and Nearest Planes in Practice needs a person (or library access).

## Phase 2b: repeated decoding attempts (added 7 Nov, late)
- de Perthuis–Trenkić 2025/2195, **full text read** (pp. 1–14). Their fix for the uSVP route: the short vector is fixed across tours, so fix its length and integrate over its distribution (beta, not chi-squared). They treat uSVP only and do not model the decoding (Babai) step or repeated decoding attempts.
- Bischof et al., Nearest Planes in Practice, **full text read**. Covers parallel runtime only; no success-probability validation.
- Wunderer, A detailed analysis of the hybrid lattice-reduction and meet-in-the-middle attack, J. Math. Cryptology 2019 ([open HTML](https://www.degruyterbrill.com/document/doi/10.1515/jmc-2016-0044/html)), **searched in full text** for "independen", "repeat", "randomiz", "amplif". Assumption 1 states: "We further assume that p(v) is equal to some constant probability p … for all v ∈ S". Repetitions are charged as T_red + T_hyb / p_succ, with a fresh reduced basis "of same quality" and the reduction paid once. That is the assumption our R4 test rejects. His experiments measure guessing success (10,000 repetitions of guessing on one lattice), not decoding over re-randomised bases.
- Wunderer PhD thesis 2018 ([TUprints](https://tuprints.ulb.tu-darmstadt.de/8082)): not read, because the PDF opens as a download.
- Liu, Nguyen, Solving BDD by Enumeration: An Update, CT-RSA 2013: paywalled, **not read**. Secondary sources say re-randomisation for BDD (extreme pruning) was discussed and is costly because BKZ must be re-run. Whether they treat the fixed error's effect on success across randomised bases is unknown.

- Liu, Nguyen 2013 again: only the abstract is reachable ([Springer](https://link.springer.com/chapter/10.1007/978-3-642-36095-4_19), purchase needed; ResearchGate returns 403). The abstract says they solve BDD by enumeration with Gama–Nguyen–Regev extreme pruning. GNR's analysis (from memory, not re-read) takes a target of fixed length in a uniformly random direction and treats re-randomised bases as independent trials. That is the same conditional computation as our "exact fixed-norm law". **So that computation is prior art in spirit and is not claimed as new.** Liu–Nguyen may fix ‖e‖ at its expected value or integrate over it; unknown until the full text is read.
- What remains as a candidate contribution: measuring that repeated decoding attempts are dependent; showing that for BKZ bases conditioning on each instance's own ‖e‖ explains all of it (to be confirmed by R7); and showing that the lattice estimator's per-level product with constant-p repetitions (Wunderer's Assumption 1) is biased per instance and right on average only by cancellation.

## Verdict (8 Nov 2026)
The claimed contribution is: (1) repeated Babai attempts on one LWE instance are dependent, in 8 of 8 settings, against Wunderer's Assumption 1 and the lattice estimator's amplify(); (2) for BKZ bases, conditioning on each instance's ‖e‖ with the exact joint law accounts for all of it, confirmed by the pre-registered R8 on fresh instances. Of the sources that could be read, none contains this: 2025/2195 (uSVP only), Wunderer 2019 (assumes constant p), Nearest Planes in Practice (runtime), the estimator's code (independent trials). Remaining gap: Liu–Nguyen 2013 (paywalled, abstract only). It could contain the conditional analysis for randomised BDD enumeration; it is not known to measure the dependence or to address the estimator's repetition model.

Also tried: Kirshanova–May–Wiemer, Parallel Implementation of BDD enumeration for LWE, ACNS 2016 ([ePrint 2016/380](https://eprint.iacr.org/2016/380)), which re-implements Liu–Nguyen's linear length pruning. Its abstract does not describe the success model; the PDF is behind a Cloudflare check. Also tried: Phong Nguyen's homepage ([di.ens.fr/~pnguyen](https://www.di.ens.fr/~pnguyen/)) links only to [DBLP](https://dblp.org/rec/conf/ctrsa/LiuN13), with no hosted copy. Authors per DBLP: Mingjie Liu and Phong Q. Nguyen. **To finish the prior-art check, a person needs to get the PDFs of Liu–Nguyen 2013 (CT-RSA, LNCS 7779, pp. 293–309) and of ePrint 2016/380.**

## Liu–Nguyen 2013 via a secondary source (8 Nov 2026)
Luan, Shi, Gu, Zheng, Application of Discrete Pruned Enumeration in Solving BDD, Symmetry 15(2):355, 2023 ([open access, read in full text](https://www.mdpi.com/2073-8994/15/2/355)), describes Liu–Nguyen's method and success model directly:
- Liu–Nguyen "treat BDD decoding as lattice vector enumeration in an n-dimensional ball with radius R", with R ≈ the BDD error, "a reasonable estimation of BDD error", and use GNR extreme pruning with re-randomised bases.
- Case 3 ("BDD with known error distribution"): Lindner–Peikert give the success probability "using the continuous Gaussian distribution"; "[2] [Liu–Nguyen] also adopts this method and gives the corresponding analysis for GNR enumeration".
- Luan et al.'s own models (Cases 1–3) estimate a per-round success probability and use it "on average" across re-randomised rounds, assuming stable basis quality.

So every analysis of re-randomised BDD that could be checked uses one per-attempt (averaged) success probability with independent repetitions: Lindner–Peikert 2011, Liu–Nguyen 2013 (as described by Luan et al.), Luan et al. 2023, Wunderer 2019 (Assumption 1), and the lattice estimator (amplify). None measures or models the per-instance dependence; de Perthuis–Trenkić 2025 make the analogous point for uSVP only.

**Verdict.** As far as the literature could be checked, the contribution is new: repeated decoding attempts on one instance are dependent, and for BKZ bases conditioning on the instance's ‖e‖ accounts for it (R8, pre-registered, passed). Liu–Nguyen's own text was checked only through Luan et al.'s description; reading it first-hand remains a to-do before submission.

## Liu–Nguyen 2013, read first-hand (8 Nov 2026)
Source: the user's copy of the proceedings, `978-3-642-36095-4.pdf`, pp. 293–309.

- **Sec. 3.5:** with ℓ re-randomized bases, "the success probability is also heuristically multiplied by ℓ". This is independent trials, assumed and not tested.
- **Sec. 4.1:** GNR's p_succ assumes the error is uniform on a sphere of radius R. Since ‖t−u‖ is unknown, they take R = the expected length, which they call "a rough estimate". They prefer sampling the error distribution, which gives an averaged p.
- **Sec. 4.2:** they note that e/‖e‖ is uniform and use the fixed-norm sphere probability only as a lower bound, with R_m chosen so that Pr(‖e‖ > R_m) is negligible. They never condition on an instance's own ‖e‖ across bases.
- **Sec. 4.3, GGH:** they use one BKZ basis for many instances and claim the rest "could be recovered simply by repeating our experiments a small number of times". That claim is untested.
- **Sec. 4.4, DSA:** 23 of 100 instances were solved, which they read as "multiply by roughly 4". That is the independence assumption across instances.

**Final verdict:**
- *Not new:* the fixed-norm, uniform-direction computation, which comes from GNR/LN.
- *New:* measuring that repeated attempts on one instance are dependent, and showing (R8, pre-registered) that conditioning on the instance's own ‖e‖ explains it for BKZ bases. The flaw this exposes is the "multiply by ℓ" / amplify() step used by LN13, Wunderer 2019 and the lattice estimator.

## Kirshanova–May–Wiemer 2016 and Wunderer's thesis (8 Nov 2026, later)
- **Kirshanova, May, Wiemer**, *Parallel Implementation of BDD Enumeration for LWE*, ACNS 2016 (ePrint 2016/380). Read from the user's copy, `2016-380.pdf`.
  - They explicitly do not use extreme pruning or re-randomisation: "re-randomizing an instance causes re-running the expensive BKZ reduction".
  - Their success model is per single enumeration (Lindner–Peikert d_k choice, length pruning).
  - They have no model of repeated attempts, so nothing here changes the verdict.
- **Wunderer's 2018 PhD thesis:** still not read. The file supplied, `thesis_published.pdf`, is J. Brendel, *Future-Proofing Key Exchange Protocols*, TU Darmstadt 2019 (TUprints 9642), not Wunderer's thesis.
  - The thesis's content on hybrid attacks is expected to match Wunderer 2019 (JMC), which was searched in full text and states Assumption 1 (constant p).

## Earlier verdict
Nothing read claims the validation we do. The check is not complete until the three unread texts above are checked.
