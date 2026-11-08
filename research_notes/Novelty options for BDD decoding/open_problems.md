# Open problems and recent developments in the decoding (BDD) step of lattice attacks on LWE / ML-KEM

Verification legend: **[V]** = the page was opened during this research session (Nov 2026) and its title, authors and venue were checked. **[S]** = seen only in search-result snippets. **[U]** = cited from background knowledge and not opened this session; check before citing.

## Q1. How does the primal attack finish today: uSVP/Kannan embedding vs BDD (Babai/NearestPlanes), and when is BDD-style decoding still used?

### Takeaway
The headline estimates and the practical LWE records use **uSVP via Kannan embedding**, with success predicted by the "2016 estimate" (ADPS16, validated by Albrecht et al. 2017) and refined by probabilistic BKZ simulators (DDGR20, Postlethwaite-Virdia). An explicit BDD decoding step (Babai/NearestPlanes, pruned enumeration, Slicer) survives in three places: (a) **hybrid attacks**, where you guess part of the secret and decode a reduced instance per guess, (b) **two-step "reduce then search" attacks**, and (c) **sparse/small-secret practice**, where Guess+Verify with batched Babai is the current best performer. Since 2023 this is an active area again: Bernstein 2023, the Fast Slicer at ASIACRYPT 2025, Pulles-Vié 2025, and Karenin et al. 2025.

### Cited Findings
- Albrecht, Göpfert, Virdia, Wunderer, "Revisiting the Expected Cost of Solving uSVP and Applications to LWE", ASIACRYPT 2017 (ePrint 2017/815) **[V]**. It contrasts two uSVP success conditions: Gama-Nguyen (Eurocrypt 2008) and Alkim et al. (USENIX 2016). The two "predict significantly different costs". Experiments support the 2016 estimate and explain why reduction sometimes does better than predicted. — [ePrint 2017/815](https://eprint.iacr.org/2017/815)
- Alkim, Ducas, Pöppelmann, Schwabe, "Post-quantum key exchange - a new hope", USENIX Security 2016, ePrint 2015/1092 **[U]**: source of the 2016 estimate. The lattice-estimator docstrings cite it as `[USENIX:ADPS16]`. — [ePrint 2015/1092](https://eprint.iacr.org/2015/1092)
- Postlethwaite, Virdia, "On the Success Probability of Solving Unique SVP via BKZ", PKC 2021 (ePrint 2020/1308) **[V]**. It extends the DDGR20 probabilistic simulation for Progressive BKZ to BKZ 2.0, validates it experimentally, explains the "succeeds at smaller β than expected" observations of Albrecht et al. 2017, and re-estimates the NIST KEM finalists. — [ePrint 2020/1308](https://eprint.iacr.org/2020/1308)
- Dachman-Soled, Ducas, Gong, Rossi, "LWE with Side Information: Attacks and Concrete Security Estimation", CRYPTO 2020 (ePrint 2020/292) **[V]**. The framework adds "hints" (from side channels, decryption failures or scheme constraints) to the primal attack before a final reduction. Techniques include sparsifying the lattice, projecting onto or intersecting with hyperplanes, and altering the secret's distribution. A Sage implementation (the "leaky-LWE-estimator") is provided. — [ePrint 2020/292](https://eprint.iacr.org/2020/292)
- Karenin, Kirshanova, May, Nowakowski, "Fast Slicer for Batch-CVP: Making Lattice Hybrid Attacks Practical", ASIACRYPT 2025 (ePrint 2025/1910) **[V]**:
  - It states that the plain primal attack with Kannan embedding is the current state of the art in practical LWE records.
  - It implements Bernstein's hybrid, which enumerates some key coordinates and solves the dimension-reduced instance with the batch-CVP randomized Slicer with LSH.
  - It generalizes the hybrid to BDD with error distribution D. The asymptotic speedup over primal's T = 2^{0.292d} is T^{1-K}, with K ≈ (1 + H(D)/0.058)^{-1}, where H(D) is the Shannon entropy of D.
  - Practical speedups are up to 5x for n in [160, 210] with ternary/CBD distributions.
  - For Regev's original parameters, the hybrid gives no improvement. — [ePrint 2025/1910](https://eprint.iacr.org/2025/1910)
- Bernstein, "Asymptotics of hybrid primal lattice attacks", ePrint 2023/1892 (preprint) **[V]**. It shows that standard heuristics imply hybrid primal ("multi-decoding", CVPP/BDDP) key recovery is **exponentially** faster than non-hybrid primal against LPR with any constant error width. The cost falls from 2^{ρn} to 2^{(ρ-ρH₀)n} with H₀ = 1/(1 + lg w/(0.057981 z₀)). Bernstein calls this the first such exponential speedup since 2015. — [ePrint 2023/1892](https://eprint.iacr.org/2023/1892)
- Wunderer, "Revisiting the Hybrid Attack: Improved Analysis and Refined Security Estimates", ePrint 2016/733 **[V]**. Earlier hybrid analyses set probabilities equal to 1 when the true values were as small as 2^-80. Their errors ran in both directions (over- and underestimates). Wunderer gives a corrected runtime analysis and reevaluates NTRU, NTRU Prime, R-BinLWEEnc, BLISS and GLP. The abstract does not name Howgrave-Graham. — [ePrint 2016/733](https://eprint.iacr.org/2016/733)
- Howgrave-Graham, "A Hybrid Lattice-Reduction and Meet-in-the-Middle Attack Against NTRU", CRYPTO 2007 **[U]**: the original hybrid, which runs reduction followed by MitM guessing with Babai (nearest-plane) checking. — [Springer DOI 10.1007/978-3-540-74143-5_9](https://doi.org/10.1007/978-3-540-74143-5_9) (link not opened)
- Liu, Nguyen, "Solving BDD by Enumeration: An Update", CT-RSA 2013, LNCS 7779, pp. 293-309 **[V via DBLP/search]**. Pruned enumeration for BDD gives significant improvements over Lindner-Peikert's Search-LWE (NearestPlanes) algorithm and is practical around dimension 350. The authors conclude that security estimates of BDD-based systems must take enumeration attacks into account. The lattice estimator's `primal_bdd` cites it as `[RSA:LiuNgu13]`. — [DBLP](https://dblp.org/rec/conf/ctrsa/LiuN13); [DOI 10.1007/978-3-642-36095-4_19](https://unpaywall.org/10.1007%2F978-3-642-36095-4_19)
- Lindner, Peikert, "Better Key Sizes (and Attacks) for LWE-Based Encryption", CT-RSA 2011, ePrint 2010/613 **[U]**. This is the origin of NearestPlanes with per-level branching (d_i), i.e. the team's "Lindner-Peikert per-level" decoder. — [ePrint 2010/613](https://eprint.iacr.org/2010/613)
- Xia, Wang, Wang, Gu, Wang, "A Refined Hardness Estimation of LWE in Two-step Mode", PKC 2024 (ePrint 2024/067) **[V]**:
  - It argues that combining reduction (LLL/BKZ) with a target-vector search (enumeration/sieving) is more efficient than BKZ alone.
  - It links the target vector's distribution to the two-step success rate.
  - It states that the estimator's `primal-bdd` "does not take into account some up-to-date results and lacks a thorough theoretical analysis".
  - It reports estimates 2.1-3.4 bits lower than leaky-LWE-Estimator for the NIST standards (2.2-4.6 with flexible block size and jump). — [ePrint 2024/067](https://eprint.iacr.org/2024/067)
- Pulles, Vié, "Accelerating the Primal Hybrid Attack against Sparse LWE using GPUs", ePrint 2025/1990 (preprint) **[V]**. It implements Guess+Verify (Albrecht et al., SAC 2019) with cuBLASter (GPU BKZ + G6K sieving), a **dimension-reduction technique for the BDD instance**, and a **batched Babai Nearest Plane**. It beats Cool&Cruel on almost all of the Wenger et al. benchmarks. — [ePrint 2025/1990](https://eprint.iacr.org/2025/1990)

### Inferences
- The team's result, where LLL plus a pruned 3-plane list beat BKZ-10 plus Babai at n = 80, is the small-scale version of the trade-off documented by Liu-Nguyen 2013 and Xia et al. 2024: spending effort on decoding (search) rather than on reduction can win. The "uSVP-only" estimate in the estimator does not capture this.
- In current practice, decoding is never the "plain primal" finish. It is the inner loop of the hybrid, executed once per guess (batch-CVP). So the per-call cost and success probability of the decoder multiply directly into the attack cost. This is where a better decoder pays off.

### Gaps
- I did not open Howgrave-Graham 2007, ADPS16 or Lindner-Peikert 2011 **[U]**.
- 2025/1002 and 2025/1990 cite Guess+Verify as "Albrecht et al., SAC 2019", but I did not identify or open that paper, so its exact title and author list are unverified.
- I did not open the Pulles-Vié PDF, so its exact p_babai model is unknown.

## Q2. How does the lattice estimator model decoding (primal_bdd, primal_hybrid)? Known gaps and crude approximations

### Takeaway
In `estimator/lwe_primal.py`, `primal_bdd` is just `primal_hybrid(zeta=0, mitm=False, babai=False)`, which is BKZ followed by an SVP call in a projected sublattice of dimension η (Liu-Nguyen-style), followed by Babai on the rest. The Babai success probability is derived **only from the error's standard deviation** (`prob_babai(r, sqrt(d)*Xe.stddev)`). Babai cost is a flat d² operations. A MitM success probability is marked `TODO: ... needs to be analysed`. Several gaps are written directly into the code.

### Cited Findings
(Source: lattice-estimator `estimator/lwe_primal.py`, main branch, fetched Nov 2026 **[V]**: [GitHub file](https://github.com/malb/lattice-estimator/blob/main/estimator/lwe_primal.py))
- `primal_bdd` docstring: "Estimate the cost of the BDD approach as given in [RSA:LiuNgu13]". It is implemented as `primal_hybrid(params, zeta=0, mitm=False, babai=False, ...)`.
- `svp_dimension(r, beta, D, ...)` finds the smallest η with `D.stddev**2 * eta <= exp(2*log_gh(eta, log_proj_vol))`. This is the ADPS16-style condition on the projected sublattice, using the Gaussian heuristic and only the error's standard deviation. A code comment says η = 2, 3, ... cannot be tried incrementally "because this gives issues in extremely low dimensions".
- Babai branch: η = 2, `babai_cost(d) = Cost(rop=max(d,1)**2)`, probability `prob_babai(r, sqrt(d)*Xe.stddev)`. Non-Babai branch: probability `prob_babai(r[:d-eta], sqrt(d-eta)*Xe.stddev)` plus SVP cost in dimension η.
- MitM: `mitm_babai_probability(r, Xe.stddev)` is used only when `mitm and zeta>0 and babai`. Otherwise the code says "TODO: the probability in this case needs to be analysed" and sets the probability to 1. The search-space reduction is modelled as √(search space).
- Overall success = `hit_probability * babai_probability * mitm_probability`, amplified to 0.99 by ~1/p repetitions ("Repeat whole experiment ~1/prob times"), which assumes independent trials.
- The ζ optimiser fits a parabola (`minimize_scalar`). The code warns this "can cause this search to miss minima at extrema". It also notes the cost curve in β is "non-smooth, with sudden jumps due to the search space changing".
- `primal_usvp` uses only `Xe.stddev`/`Xs.stddev` (via ξ = σ_e/σ_s, Bai-Galbraith scaling) and has a modelling convention: "if d == β we assume one SVP call, otherwise poly calls".
- Xia et al. (PKC 2024) independently criticise `primal-bdd` as lacking up-to-date results and thorough analysis. They also note it treats success across BKZ tours as independent rather than accumulating, the latter point from a search snippet **[S]**. — [ePrint 2024/067](https://eprint.iacr.org/2024/067)
- de Perthuis, Trenkić, "Refined Modelling of the Primal Attack, and Variants Against Module-Learning With Errors", PQCrypto 2026 (ePrint 2025/2195) **[V]**:
  - The DDGR20 and PV21 estimators assume the unique short vector is **resampled** during the attack, which contradicts experiments.
  - They use only the **first two moments** of secret and error, so they cannot distinguish centred distributions with equal variance.
  - Their fix is to condition on the realised length of the short vector and integrate over its distribution.
  - They also give a Module-BKZ simulator generalising Chen-Nguyen.
  - This is a uSVP-side result. BDD and decoding are not discussed. — [ePrint 2025/2195](https://eprint.iacr.org/2025/2195)

### Inferences
- Concrete gap 1: the decoding success probability uses only the standard deviation. For CBD η=2 (support {-2..2}, σ²=1) the projected error coordinates ⟨e, b_i*⟩/‖b_i*‖² are not exactly Gaussian, especially in the low-index, large-‖b_i*‖ region after weak reduction (LLL/BKZ-10) where Babai fails. An exact or Edgeworth/saddlepoint-corrected per-level failure probability for CBD/bounded errors is not in the estimator. de Perthuis-Trenkić fixed the analogous two-moment flaw only for uSVP.
- Concrete gap 2: the estimator has no cost/success model for **list or pruned decoders** (Lindner-Peikert d_i, beam search, likelihood-pruned enumeration). Its only options are Babai (d² ops) or "SVP in dimension η" via a reduction cost model. The team's decoders sit in an unmodelled middle ground.
- Concrete gap 3: the MitM probability TODO and the independence/√ assumptions in the hybrid are acknowledged open items in the tool itself.
- I have not checked the exact formula inside `prob_babai` (in `estimator/prob.py`). From background knowledge **[U]** it is a product over GSO levels of per-coordinate Gaussian probabilities that the projected error falls in [-‖b_i*‖/2, ‖b_i*‖/2). Verify before citing.

### Gaps
- I did not open `estimator/prob.py` or the estimator's ReadTheDocs pages this session.
- I found no published systematic validation of `primal_hybrid`'s Babai/MitM probabilities against experiments at small n. This looks like a genuine gap the team's benchmark could fill.

## Q3. Recent work on the trade-off between reduction strength and decoding effort, dual-attack controversy, sparse secrets, Cool + Cruel = Dual

### Takeaway
From 2023 to 2026 the field moved toward: (i) recognising that decoding-side heuristics can be badly wrong (the dual-sieve controversy); (ii) making hybrid/decoding attacks practical (Slicer, batched Babai on GPU, BDD dimension reduction); and (iii) showing that correctly parametrised primal and decoding attacks beat newer ML and "C+C" attacks on sparse LWE. The explicit reduction-versus-decoding trade-off is addressed by Xia et al. (two-step), Liu-Nguyen (pruned BDD) and the hybrid line, but no work gives a unified analysis for discrete error distributions.

### Cited Findings
- Ducas, Pulles, "Does the Dual-Sieve Attack on Learning with Errors even Work?", ePrint 2023/302 (CRYPTO 2023 per background **[U]** for the venue) **[V]**:
  - It generalises the Guo-Johansson/MATZOV FFT trick to arbitrary BDD instances.
  - It shows the heuristics behind Dual-Sieve-FFT contradict theorems in some regimes and well-tested heuristics in others.
  - Experiments reveal a "waterfall-floor" phenomenon.
  - Its conclusion: the success probabilities of recent dual-sieve-FFT attacks are likely significantly overestimated. — [ePrint 2023/302](https://eprint.iacr.org/2023/302)
- Karenin, Kirshanova, Nowakowski, Postlethwaite, Pulles, Virdia, Vié, "Cool + Cruel = Dual, and New Benchmarks for Sparse LWE", ePrint 2025/1002 (preprint; received 2025-05-30, revised 2025-11-04) **[V]**. It shows that C+C (Nolte et al.) is an instance of Albrecht's EUROCRYPT 2017 dual attack and attributes the C+C effect to the Z-shaped q-ary basis geometry. It **introduces a dimension-reduction framework for BDD "of independent interest"**. It shows a correctly parametrised primal attack (Drop+Solve, May-Silverman CaLC 2001; Guess+Verify, Albrecht et al. SAC 2019) beats C+C, and open-sources both. — [ePrint 2025/1002](https://eprint.iacr.org/2025/1002)
- Wenger, Saxena, Malhou, Thieu, Lauter, "Benchmarking Attacks on Learning with Errors", IEEE S&P 2025 (ePrint 2024/1229) **[V]**. uSVP recovered no secrets after more than 1100 hours on their Kyber-like settings. SALSA and C+C recovered binomial secrets of Hamming weight 9-11 for Kyber (κ=2) in 28-36 hours. Dual Hybrid MitM solved decision instances up to Hamming weight 4 in under an hour. The page does not mention BDD or primal hybrid; 2025/1002 and 2025/1990 later argue the primal baseline was mis-parametrised. — [ePrint 2024/1229](https://eprint.iacr.org/2024/1229)
- Pulles, Vié, ePrint 2025/1990 **[V]**: Guess+Verify with batched Babai and BDD dimension reduction beats C+C on almost all Wenger et al. instances. — [ePrint 2025/1990](https://eprint.iacr.org/2025/1990)
- Bernstein, "Asymptotics for the standard block size in primal lattice attacks: second order, formally verified", ePrint 2024/592 **[S]**. — [ePrint 2024/592](https://eprint.iacr.org/2024/592)
- "An Improved Hybrid Dual Attack on LWE with ..." ePrint 2026/1060 **[S]**. The title was truncated in search and the page was not opened. — [ePrint 2026/1060 PDF](https://eprint.iacr.org/2026/1060.pdf)
- Budroni, Mårtensson, "Improved Estimation of Key Enumeration with Applications to Solving LWE", ePrint 2023/139 **[V]**. It computes the expected key-enumeration cost in polynomial time and applies it to the guessing part of the **dual** attack (Kyber, Saber, TFHE), lowering estimates. — [ePrint 2023/139](https://eprint.iacr.org/2023/139)

### Inferences
- The decoding-side "dimension reduction for BDD" appears independently in 2025/1002 and 2025/1990. It is fresh and probably not yet incorporated in the lattice estimator. Analysing how it interacts with list or pruned decoders is an open niche.
- Budroni-Mårtensson's exact enumeration-order cost for the dual guess has an obvious primal-hybrid and decoder-side analogue that I did not find: the expected cost of a likelihood-ordered list decoder over CBD coordinates.

### Gaps
- I did not find a 2022-2026 paper that explicitly optimises the joint (BKZ β, decoder list size / pruning) trade-off for the primal BDD finish with discrete errors. Xia et al. 2024 is closest, but I only read its abstract.

## Q4. Decoders exploiting the exact discrete error distribution (CBD, bounded support) or the module structure of ML-KEM

### Takeaway
Exploiting the error distribution appears in the literature mainly through **entropy** (Bernstein 2023; the Fast Slicer's K depends on H(D)), **hints / altered distributions** (DDGR20), and **higher-moment-aware uSVP modelling** (de Perthuis-Trenkić). Module structure is used in Module-BKZ simulation (de Perthuis-Trenkić) but not in decoding. I found **no** paper that builds a BDD/NearestPlanes/list decoder with a maximum-likelihood or a-posteriori metric matched to the CBD and analyses its success probability. This looks like a genuine gap.

### Cited Findings
- Fast Slicer hybrid: the asymptotic gain depends on the Shannon entropy H(D) of the error/secret distribution. Experiments use ternary and centered binomial distributions. — [ePrint 2025/1910](https://eprint.iacr.org/2025/1910) **[V]**
- Bernstein's hybrid exponent depends on the error width w via H₀. — [ePrint 2023/1892](https://eprint.iacr.org/2023/1892) **[V]**
- Two-moment limitation of current primal estimators and the module primal attack (Module-BKZ simulator). The claimed subexponential gain applies when |Δ_K| < d^d, highlighted for non-power-of-two cyclotomics, so it does not directly cover Kyber's power-of-two ring. — [ePrint 2025/2195](https://eprint.iacr.org/2025/2195) **[V]**
- DDGR20 integrates side information by "altering the secret's distribution" and through hyperplane intersections (a Bayesian-flavoured update). — [ePrint 2020/292](https://eprint.iacr.org/2020/292) **[V]**
- "Belief Propagation Meets Lattice Reduction: Security Estimates for Error-Tolerant Key Recovery from Decryption Errors" combines BP over the discrete Kyber distribution with lattice reduction, but in a side-channel/decryption-failure setting. — [ResearchGate](https://www.researchgate.net/publication/373569142_Belief_Propagation_Meets_Lattice_Reduction_Security_Estimates_for_Error-Tolerant_Key_Recovery_from_Decryption_Errors) **[S]** (authors and venue not verified)
- "On the Security of LWE-based KEMs under Various Distributions", ePrint 2024/1979: how secret/error distribution choice affects hardness and decryption failure, compared against Kyber's CBD. — [ePrint 2024/1979](https://eprint.iacr.org/2024/1979.pdf) **[S]**
- ML-KEM uses CBD with η₁ ∈ {3, 2, 2} and η₂ = 2, q = 3329 (FIPS 203) **[U]**. — [FIPS 203](https://csrc.nist.gov/pubs/fips/203/final)

### Inferences
- The team's "beam search with likelihood pruning" is essentially a K-best / sphere decoder with a prior, as in MIMO communications (inference; no crypto paper found that frames it this way). A CBD-matched metric (log P_CBD of the reconstructed error, not Euclidean distance) plus a closed-form per-level failure probability would cover two gaps at once: the estimator's stddev-only `prob_babai`, and the absence of list decoders in cost models.
- Bounded support (|e_i| ≤ 2) gives hard constraints that a Gaussian model ignores. Interval or box-constrained NearestPlanes, and pruning on infeasible partial errors, is a plausible small, testable contribution. I found no paper on it.
- Module structure: using rotations (the X^k·s trick, also in DDGR20-style hints) to get multiple BDD targets from one basis, i.e. batch decoding, is a natural fit for batched Babai or Slicer. I found no analysis of this for the decoding step specifically.

### Gaps
- My search ("lattice decoding LWE centered binomial ... pruning") returned no direct hit. "Lattice Decoding Attacks on Binary LWE" (Bai-Galbraith, ACISP 2014 **[U]**) appeared only as a reference title. Absence of evidence after one search is weak, so the team should run a targeted search on terms like "sphere decoding LWE", "K-best LWE", "MAP decoding lattice LWE", and "soft-output Babai".

## Q5. Open questions stated in recent papers about decoding / BDD / the last step

### Takeaway
The open questions stated explicitly are few but pointed. (1) Bernstein: what exponent do more sophisticated hybrids reach, and what is the impact on Kyber-512, whose analyses ignored hybrids? (2) The estimator's own TODO: the hybrid MitM success probability is not analysed. (3) Ducas-Pulles: decoding-side heuristics (dual-sieve-FFT) are untrustworthy and their regime of validity is unclear. (4) Fast Slicer: hybrids can lose to primal in some regimes (Regev parameters), so the crossover is distribution-dependent.

### Cited Findings
- Bernstein raises "what exponent more sophisticated hybrid attacks achieve" and "what impact hybrid attacks have on concrete systems such as Kyber-512, whose security analyses ignored them" (paraphrased from the abstract). — [ePrint 2023/1892](https://eprint.iacr.org/2023/1892) **[V]**
- Estimator: "TODO: the probability in this case needs to be analysed" (hybrid without Babai+MitM). The ζ-search can miss minima, and the cost curve has jumps. — [lattice-estimator lwe_primal.py](https://github.com/malb/lattice-estimator/blob/main/estimator/lwe_primal.py) **[V]**
- Dual-Sieve-FFT success probabilities are likely significantly overestimated, and there is an unexplained "waterfall-floor" phenomenon. — [ePrint 2023/302](https://eprint.iacr.org/2023/302) **[V]**
- The hybrid cannot improve over primal for Regev's original parameters. The gain constant K can be small for high-entropy distributions. — [ePrint 2025/1910](https://eprint.iacr.org/2025/1910) **[V]**
- Prior hybrid analyses set probabilities to 1 when they were as small as 2^-80. — [ePrint 2016/733](https://eprint.iacr.org/2016/733) **[V]**
- `primal-bdd` "lacks a thorough theoretical analysis". — [ePrint 2024/067](https://eprint.iacr.org/2024/067) **[V]**

### Inferences (candidate research contributions, ranked by feasibility for a student team)
1. **Exact-distribution success model for NearestPlanes/list decoders.** Derive and validate the per-level failure probability for CBD(η) errors on simulated or real GSO profiles (LLL, BKZ-β), and compare against the estimator's stddev-only `prob_babai`. This is low cost, testable at n ≤ 100, and fills a documented gap; it is the decoding analogue of de Perthuis-Trenkić 2025/2195.
2. **Cost/success model for pruned list decoders** (Lindner-Peikert d_i, beam, likelihood-pruned), as a third option between "Babai" and "SVP in dimension η" in `primal_hybrid`. The team's n = 80 result (LLL + pruned list > BKZ-10 + Babai) is direct motivating evidence. Validate against Liu-Nguyen-style pruned enumeration.
3. **Empirical validation of the estimator's hybrid probabilities** (`mitm_babai_probability`, the √-search-space assumption, and the independence used in `prob_amplify`) at toy sizes. No such validation was found.
4. **Box-constrained / MAP decoding** that uses bounded CBD support. It could combine with BDD dimension reduction (2025/1002, 2025/1990) and batch decoding over module rotations.
5. Longer-term: the hybrid exponent and Kyber-512 question (Bernstein), which needs Slicer-scale experiments (2025/1910). This is likely beyond a student project.

### Gaps
- I did not read the conclusion sections of the PDFs (2025/1910, 2025/1002, 2025/1990, 2024/067, 2025/2195), only their abstracts or landing pages. More explicitly stated open questions are likely there.
- I could not verify whether newer 2026 ePrints, beyond 2026/1060 (unopened) and the PQCrypto 2026 version of 2025/2195, address CBD-aware decoding.
- The Kyber round-3 specification's hybrid-attack discussion was not opened: [Kyber spec round 3](https://pq-crystals.org/kyber/data/kyber-specification-round3-20210131.pdf) **[S]**.
