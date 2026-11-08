# Graph Report - ABHILASH CRYPTO PROJECT  (2026-11-08)

## Corpus Check
- Large corpus: 55 files · ~1,072,368 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 368 nodes · 679 edges · 17 communities (14 shown, 3 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 108 edges (avg confidence: 0.84)
- Token cost: 348,106 input · 0 output

## Community Hubs (Navigation)
- Decoding Study Code
- VA-ANP Stress Tests
- Toy LWE Experiments
- Retry Tests R6-R9
- Liu-Nguyen BDD Enumeration
- BKZ Convergence & Estimator
- CVP Decoder Prototypes
- MIMO Tree-Search Directions
- Per-Noise VA-ANP Check
- Decoding Study Findings
- GPU Decoding & Venues
- Hybrid Attack Open Problems
- Babai & Pruning Models
- Toy LWE Results
- CBD-Aware Candidate Selection
- Retry Success Models
- Babai Decoder Stub

## God Nodes (most connected - your core abstractions)
1. `Report: Measure the decoding step, stop reinventing decoders` - 17 edges
2. `Solving BDD by Enumeration: An Update (Liu-Nguyen, CT-RSA 2013)` - 15 edges
3. `v2_dim()` - 13 edges
4. `Retry study: are repeated decoding attempts independent?` - 12 edges
5. `expD()` - 11 edges
6. `run_job()` - 11 edges
7. `Open problems in the BDD decoding step notes` - 11 edges
8. `VA-ANP beam search over Babai nearest plane` - 11 edges
9. `run_experiment()` - 10 edges
10. `expA()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `VA-ANP beam search over Babai nearest plane` --semantically_similar_to--> `GNR pruned enumeration for BDD (Alg. 4)`  [INFERRED] [semantically similar]
  research_notes/Novelty options for BDD decoding/prior_art.md → 978-3-642-36095-4.pdf
- `Exact fixed-norm law (retry_exact.py)` --semantically_similar_to--> `Fixed-norm uniform-sphere success lower bound`  [INFERRED] [semantically similar]
  Retry_study_summary.md → 978-3-642-36095-4.pdf
- `Shim-Kang probabilistic tree pruning (IEEE TSP 2008)` --semantically_similar_to--> `Gama-Nguyen-Regev extreme pruning (EUROCRYPT 2010)`  [INFERRED] [semantically similar]
  research_notes/Novelty options for BDD decoding/prior_art.md → 978-3-642-36095-4.pdf
- `Exact fixed-norm law (retry_exact.py)` --semantically_similar_to--> `de Perthuis-Trenkic refined primal modelling (PQCrypto 2026, ePrint 2025/2195)`  [INFERRED] [semantically similar]
  Retry_study_summary.md → research_notes/Novelty options for BDD decoding/open_problems.md
- `Q2 verdict: VA-ANP adaptive wins vs all baselines at 2 of 6 => rule FAILED` --semantically_similar_to--> `Dim 40 verdict: VA-ANP adaptive 0.97x nodes vs Beam fixed => FAIL`  [INFERRED] [semantically similar]
  toy_lwe_results.txt → stress_test_v2_results.txt

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Independent-trials repetition assumption across re-randomised bases** — 978_3_642_36095_4_randomized_nearestplanes, research_notes_novelty_check_phase2_wunderer_assumption_1, research_notes_novelty_options_for_bdd_decoding_open_problems_estimator_amplify, retry_study_summary_r4_independence_rejected, research_notes_novelty_check_phase2_contribution_verdict [EXTRACTED 1.00]
- **VA-ANP ingredients and their published ancestors** — research_notes_novelty_options_for_bdd_decoding_prior_art_va_anp, research_notes_novelty_options_for_bdd_decoding_prior_art_lindner_peikert_nearestplanes, research_notes_novelty_options_for_bdd_decoding_prior_art_klein_lls_sampling, research_notes_novelty_options_for_bdd_decoding_prior_art_t_algorithm, 978_3_642_36095_4_gnr_pruned_enumeration_for_bdd, research_notes_novelty_options_for_bdd_decoding_prior_art_luan_discrete_pruning_bdd [EXTRACTED 1.00]
- **Conditioning success on the realised error/short-vector length** — retry_study_summary_exact_fixed_norm_law, 978_3_642_36095_4_fixed_norm_sphere_lower_bound, research_notes_novelty_options_for_bdd_decoding_open_problems_de_perthuis_trenkic, retry_study_summary_per_level_product_bias [INFERRED 0.85]
- **Pre-registered retry-model tests R4-R9** — retry_study_log_r4_rejected, retry_study_log_r5_fixed_wins_false, retry_exact_heldout_log_r6, retry_exact_confirm_log_r7, retry_exact_confirm2_log_r8, retry_exact_confirm_lll_log_r9 [INFERRED 0.85]
- **VA-ANP node-efficiency claim tested and failed at scale** — stress_test_results_larger_dims, stress_test_v2_results_dim40_fail, stress_test_v2_noise_results_per_noise_comparison, toy_lwe_results_q2_verdict [INFERRED 0.75]
- **CVP decoders compared across experiments** — stress_test_results_babai_np, stress_test_results_anp, stress_test_results_va_anp, stress_test_results_lp_decoder, stress_test_v2_results_beam_decoder [INFERRED 0.85]

## Communities (17 total, 3 thin omitted)

### Community 0 - "Decoding Study Code"
Cohesion: 0.05
Nodes (33): calibrate(), calibrate_one(), cbd_logpmf(), check(), dump_profiles(), got_flags(), instance(), level_models() (+25 more)

### Community 1 - "VA-ANP Stress Tests"
Cohesion: 0.09
Nodes (37): generate_qary_lattice(), Notebook reproduction check (seed 42, ANP 253 / VA-ANP 252 of 360), bank(), _cfg_job(), cheapest(), cluster_boot(), compare(), evaluate() (+29 more)

### Community 2 - "Toy LWE Experiments"
Cohesion: 0.09
Nodes (32): Q2 verdict: VA-ANP adaptive wins vs all baselines at 2 of 6 => rule FAILED, babai_formula(), beta_name(), cbd(), choose(), cluster_boot(), gso(), heldout_stage() (+24 more)

### Community 3 - "Retry Tests R6-R9"
Cohesion: 0.07
Nodes (25): R8 test (BKZ-20 n=95, BKZ-10 n=85): exact model 0 OFF, independent 12 OFF, Multiset retry model, R9 test (LLL n=78, K=128): FAILED (multiset off 2 cells, exact 6, independent 7), R7 test (BKZ-15 n=90, BKZ-20 n=110): exact 0 OFF but var check fails, R6_pass False, Exploratory exact-model run (LLL n=80, BKZ-20 n=100): exact 5 OFF, R6 fail, R6 held-out test (LLL n=76, BKZ-10 n=90): exact 8 OFF, R6_pass False, Retry success models: independent / product / exact, heldout_path() (+17 more)

### Community 4 - "Liu-Nguyen BDD Enumeration"
Cohesion: 0.15
Nodes (18): BKZ 2.0 (Chen-Nguyen 2011) reduction estimates, DSA with 2 known nonce bits via HNP and pruned enumeration, GGH challenge key/message recovery by pruned enumeration, Gama-Nguyen-Regev extreme pruning (EUROCRYPT 2010), Hidden Number Problem lattice reduction to BDD, Schnorr random sampling (STACS 2003), Solving BDD by Enumeration: An Update (Liu-Nguyen, CT-RSA 2013), Sublattice attack (optimal m') (+10 more)

### Community 6 - "CVP Decoder Prototypes"
Cohesion: 0.15
Nodes (8): adaptive_nearest_planes(), babai_nearest_plane(), babai_roundoff(), generate_bdd_instance(), gram_schmidt(), lindner_peikert(), lll_reduce(), run_experiment()

### Community 7 - "MIMO Tree-Search Directions"
Cohesion: 0.15
Nodes (14): Direction 6: best-first stack/Fano search with bias term, Report: Measure the decoding step, stop reinventing decoders, Bai-Galbraith scaled embedding (ACISP 2014), Chang-Wen-Xie: LLL raises Babai success, SQRD may lower it, Murugan et al. MMSE-Fano unified tree search (IEEE TIT 2006), Howgrave-Graham hybrid reduction + MitM attack (CRYPTO 2007), Albrecht-Curtis-Wunderer batch BDD trade-offs (SAC 2019), Klein / Liu-Ling-Stehle decoding by sampling (+6 more)

### Community 8 - "Per-Noise VA-ANP Check"
Cohesion: 0.18
Nodes (10): acc(), cheapest_reaching(), Fixed ANP thr=0.7 vs per-noise re-picked threshold vs VA llr=2.2 (overall work 0.97x), work(), ANP (adaptive nearest plane) decoder, Exact CVP ceiling 68.8% for any decoder, Larger dims 20-40: VA-ANP speedup shrinks to 1.08x with accuracy loss, VA-ANP wrong-sigma sensitivity (exp B) (+2 more)

### Community 9 - "Decoding Study Findings"
Cohesion: 0.18
Nodes (13): BDD_decoding_study.ipynb, Exact CBD error model: null result, converge_test.py BKZ convergence test, Decoding-step study summary (7 Nov 2026), Estimator Babai prediction off due to under-reduced BKZ bases, Africacrypt 2027 (deadline 15 Jan 2027), Direction 1: decoding-step validation vs estimator, Direction 2: exact-CBD success and cost model (+5 more)

### Community 10 - "GPU Decoding & Venues"
Cohesion: 0.20
Nodes (12): Direction 4: bit-exact batch-CVP GPU beam decoder artifact, TU Darmstadt LWE challenge, Ducas-Pulles dual-sieve waterfall-floor (CRYPTO 2023), Esseissah-Bhery-Bahig GPU BDD for LWE (IEEE Access 2020), Fast Slicer for Batch-CVP (ASIACRYPT 2025, ePrint 2025/1910), G6K-GPU sieving (Ducas-Stevens-van Woerden 2021), IACR Communications in Cryptology, GPU decoding, LWE benchmarks and venues notes (+4 more)

### Community 11 - "Hybrid Attack Open Problems"
Cohesion: 0.22
Nodes (10): Direction 5: soft-output list decoder feeding hybrid/hints, List sphere decoder with soft output (Hochwald-ten Brink 2003), Bernstein asymptotics of hybrid primal attacks (ePrint 2023/1892), DDGR LWE with side information / hints (CRYPTO 2020), lattice-estimator lwe_primal.py (primal_bdd / primal_hybrid), Open problems in the BDD decoding step notes, uSVP via Kannan embedding (2016 estimate), Wunderer hybrid attack analysis (ePrint 2016/733; JMC 2019) (+2 more)

### Community 13 - "Toy LWE Results"
Cohesion: 0.25
Nodes (8): Babai success calibration vs gauss/sphere/cbd error models, LP16384 list decoding success (e.g. BKZ-20 n=100 eta=2 47.2% vs Babai 4.1%), LP (Lindner-Peikert style) list decoder, Babai predicted success formula (GS-based), BKZ 'infinite loop in babai' aborts; fixed by long double, Toy LWE pilot grid (LLL/BKZ-10/BKZ-20, n=40-130), Q1 verdict: list decoder beats Babai at 6 of 6 settings, Seconds per recovered secret (exploratory)

### Community 14 - "CBD-Aware Candidate Selection"
Cohesion: 0.36
Nodes (7): CBD prior / box candidate selection: null result, Direction 3: CBD-aware leaf rescoring and box feasibility, Box-constrained ILS (Chang-Han 2008), Deep-learning aided sphere decoding (Nguyen-Lee-Dai), Infinity-norm sphere decoding (Seethaler-Bolcskei 2010), MIMO detection techniques as BDD candidates notes, Wang-Ling Metropolis-Klein MCMC BDD (IEEE TIT 2019)

### Community 15 - "Retry Success Models"
Cohesion: 0.33
Nodes (5): R5: product-over-levels fixed-error model (failed), R6 held-out test (failed on LLL), R7 BKZ confirmation (failed on degenerate setting), R8 BKZ confirmation with degeneracy guard (passed), R9 block-multiset law for LLL (failed narrowly)

## Knowledge Gaps
- **40 isolated node(s):** `Hidden Number Problem lattice reduction to BDD`, `Sublattice attack (optimal m')`, `converge_test.py BKZ convergence test`, `BDD_decoding_study.ipynb`, `retry_study.py (pre-registered rules and code)` (+35 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 130 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Report: Measure the decoding step, stop reinventing decoders` connect `MIMO Tree-Search Directions` to `Liu-Nguyen BDD Enumeration`, `Decoding Study Findings`, `GPU Decoding & Venues`, `Hybrid Attack Open Problems`, `CBD-Aware Candidate Selection`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `Solving BDD by Enumeration: An Update (Liu-Nguyen, CT-RSA 2013)` connect `Liu-Nguyen BDD Enumeration` to `Hybrid Attack Open Problems`, `Babai & Pruning Models`, `CBD-Aware Candidate Selection`, `MIMO Tree-Search Directions`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `VA-ANP 2.59x faster than ANP, ANP-only wins 54 vs 15 (McNemar p~0)` connect `Per-Noise VA-ANP Check` to `VA-ANP Stress Tests`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Report: Measure the decoding step, stop reinventing decoders` (e.g. with `GPU decoding, LWE benchmarks and venues notes` and `MIMO detection techniques as BDD candidates notes`) actually correct?**
  _`Report: Measure the decoding step, stop reinventing decoders` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `v2_dim()` (e.g. with `_cfg_job()` and `_exact_job()`) actually correct?**
  _`v2_dim()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `expD()` (e.g. with `stress_test_va_anp.py` and `generate_qary_lattice()`) actually correct?**
  _`expD()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Hidden Number Problem lattice reduction to BDD`, `Sublattice attack (optimal m')`, `converge_test.py BKZ convergence test` to the rest of the system?**
  _40 weakly-connected nodes found - possible documentation gaps or missing edges._