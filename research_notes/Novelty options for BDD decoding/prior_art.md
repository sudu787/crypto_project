# Prior art for list/pruned decoders for BDD and approximate CVP (lattice cryptanalysis and lattice/MIMO decoding)

Scope: map prior work relevant to VA-ANP, a beam search over Babai's nearest plane. VA-ANP takes up to 3 Schnorr-Euchner planes per Gram-Schmidt level, keeps a plane if its extra squared distance is <= llr * 2*sigma^2 relative to the nearest plane, prunes candidates whose accumulated distance exceeds the best candidate's by more than T * 2*sigma^2, and caps the list size.

Closeness axes used throughout:
- (a) per-level plane selection from ||b*_i|| and sigma
- (b) per-node, target-dependent plane selection
- (c) likelihood/threshold pruning of a breadth-first list
- (d) sphere-radius pruning
- (e) use as the final step of the primal LWE attack

Verification legend:
- [V-full]: I opened the full text.
- [V-abs]: I opened the publisher, ePrint or arXiv abstract page, or retrieved the abstract from OpenAlex.
- [V-meta]: I confirmed only the bibliographic metadata, via Crossref, OpenAlex or Semantic Scholar.
- [UNVERIFIED]: I could not open any record for the item.

The MDPI, Springer full text, IEEE Xplore and most ePrint PDF downloads were blocked (HTTP 403 or bot checks). Where a claim about content goes beyond what I opened, I mark it as inference or as coming from memory.

## Q1. Lindner-Peikert NearestPlanes (CT-RSA 2011): how are the d_i chosen? Per level only, or ever target-dependent?

### Takeaway
NearestPlanes takes a fixed, user-supplied vector d = (d_1..d_k) of plane counts, one per Gram-Schmidt level. At level i it always recurses on the d_i integers closest to the projected coefficient. The d_i are chosen offline from ||b*_i|| and the error parameter s. In the paper the heuristic is to maximise min_i d_i*||b*_i|| or the erf-product success probability, under a runtime budget of prod d_i. The choice is not adaptive to the target or to the node. This is prior art for axis (a) and for (e), and it explicitly is not (b), (c) or (d).

### Cited Findings
- **Reference [V-full].**
  - Authors and title: R. Lindner and C. Peikert, "Better Key Sizes (and Attacks) for LWE-Based Encryption".
  - Venue: CT-RSA 2011, LNCS 6558, Springer, DOI 10.1007/978-3-642-19074-2_21.
  - Full version: IACR ePrint 2010/613.
  - Sources: [ePrint](https://eprint.iacr.org/2010/613); [author PDF](https://web.eecs.umich.edu/~cpeikert/pubs/lwe-analysis.pdf); DOI confirmed via [Crossref](https://api.crossref.org/works/10.1007/978-3-642-19074-2_21).
- **Algorithm (Section 4).**
  - Input: a basis B, a vector d in (Z+)^k, and a target t.
  - Step: at level k, "let c_1,...,c_{d_k} be the d_k distinct integers closest to <b*_k, v>/<b*_k, b*_k>". Recurse on each of them.
  - Output: prod d_i lattice vectors. Lemma 4.1 says this is exactly the set of v with t in v + P_1/2(B*diag(d)). That set is a rectangular box with axis lengths d_i*||b*_i||.
  - Source: [LP11 PDF, Sec. 4](https://web.eecs.umich.edu/~cpeikert/pubs/lwe-analysis.pdf).
- **Rule for choosing d_i.** The rule depends only on per-level geometry: "one should choose the multiples d_i so as to maximize min_i(d_i*||b*_i||)" — [LP11, Sec. 4](https://web.eecs.umich.edu/~cpeikert/pubs/lwe-analysis.pdf).
- **Success probability (Eq. 4.1).** For a continuous Gaussian error with parameter s, the probability is prod_i erf(d_i*||b*_i||*sqrt(pi)/(2s)).
  - The sqrt(pi) symbol was garbled in my text extraction. It is confirmed by the paper's own worked value erf(sqrt(pi)/8) ~ 0.25.
  - The paper notes that the Gaussian parameter s relates to the standard deviation by sigma = s/sqrt(2*pi).
  - Running time is "essentially prod d_i times" that of Babai.
  - Source: [LP11](https://web.eecs.umich.edu/~cpeikert/pubs/lwe-analysis.pdf).
- **Footnote 4 contrasts LP with Klein.** Klein "selects the planes at each stage probabilistically". LP is "tailored specifically to the setting where we know the distribution of the offset vector", so that it recurses "on exactly those planes that maximize the probability of success (over the choice of the error vector)". The choice is made over the error distribution, not per instance. Source: [LP11](https://web.eecs.umich.edu/~cpeikert/pubs/lwe-analysis.pdf).
- **Footnote 5 anticipates a ball-shaped search.** LP note that one could generalise to search "within an approximate ball made up of 'bricks' that are copies of P_1/2(B)". They did not do it because it "would significantly complicate the analysis". Source: [LP11](https://web.eecs.umich.edu/~cpeikert/pubs/lwe-analysis.pdf).
- **Use in the attack.** LP use the method as the decoding step after BKZ ("decoding (i.e., message and randomness recovery) attack"), with tables giving the number of NearestPlanes enumerations per attack. This is axis (e). Source: [LP11, Sec. 5 / Fig. 4](https://web.eecs.umich.edu/~cpeikert/pubs/lwe-analysis.pdf).
- **Follow-up implementation [V-full].** C. Bischof, J. Buchmann, Ö. Dagdelen, R. Fitzpatrick, F. Göpfert and A. Mariano, "Nearest Planes in Practice", BalkanCryptSec 2014, LNCS 9024, pp. 203-215 (Springer 2015), DOI 10.1007/978-3-319-21356-9_14.
  - They give the first parallel NearestPlanes. Their implementation keeps a fixed d vector ("the entries of d should be chosen to maximize min_i(d_i*||b*_i||)").
  - They report a speedup above 11x on 16 cores.
  - Sources: [PDF](https://download.hrz.tu-darmstadt.de/media/FB20/Dekanat/Publikationen/Crossing/Nearest_Planes_in_Practice.pdf); [Springer](https://link.springer.com/chapter/10.1007/978-3-319-21356-9_14); [Crossref](https://api.crossref.org/works/10.1007/978-3-319-21356-9_14).

### Inferences
- VA-ANP's rule "at most 3 planes per level, chosen from ||b*_i|| and sigma" in its per-level (non-adaptive) form is essentially LP's d-vector with d_i in {1,2,3}. It cannot be claimed as new.
- LP never thresholds on accumulated distance and never adapts to the target. So the difference between VA-ANP and LP lies in the per-node test and the likelihood list pruning, not in the use of ||b*_i|| and sigma.
- LP's "bricks approximating a ball" remark (footnote 5) shows that the idea of moving from a box-shaped to a ball-like search region was already articulated in 2011.

### Gaps
- Whether LP give an explicit optimisation procedure for d (beyond "maximise min d_i*||b*_i||" plus a runtime budget). I read Section 4 and only skimmed Section 5.

## Q2. Liu-Nguyen "Solving BDD by Enumeration: An Update" (CT-RSA 2013): what pruning does it use, and how does it relate to NearestPlanes?

### Takeaway
Liu-Nguyen recast LP's NearestPlanes as an instance of enumeration and replaced it with pruned enumeration for BDD. That means GNR-style bounding functions on the projected partial distance (a sphere-type radius per level), including linear pruning and extreme pruning with basis rerandomisation. They report large improvements over LP. This is the canonical crypto prior art for (d) and (e). It is a depth-first enumeration with absolute per-level radii. It is not a breadth-first list with pruning relative to the best candidate.

### Cited Findings
- **Reference [V-abs].**
  - Authors and title: M. Liu and P. Q. Nguyen, "Solving BDD by Enumeration: An Update".
  - Venue: CT-RSA 2013, LNCS 7779, pp. 293-309, DOI 10.1007/978-3-642-36095-4_19.
  - Sources: [Springer page](https://link.springer.com/chapter/10.1007/978-3-642-36095-4_19); [Crossref](https://api.crossref.org/works/10.1007/978-3-642-36095-4_19).
- **Abstract, paraphrased.** They apply "enumeration with pruning, including Gama-Nguyen-Regev's extreme pruning" to BDD. They report "significant improvements upon Lindner-Peikert's Search-LWE algorithm". They update the DSA-with-partially-known-nonces and GGH challenge results. They argue that BDD enumeration is practical around dimension 350 and must enter security estimates. Source: [Springer page](https://link.springer.com/chapter/10.1007/978-3-642-36095-4_19).
- **Relation to NearestPlanes, secondary source [V-full].** Bischof et al. say Liu-Nguyen "show that nearest planes can be viewed as an instance of enumeration" and apply "randomization and pruning" to it. In their reading, LN aim "to minimize the number of false positives" returned by nearest planes. Source: [Bischof et al. 2015](https://download.hrz.tu-darmstadt.de/media/FB20/Dekanat/Publikationen/Crossing/Nearest_Planes_in_Practice.pdf).
- **Name of the LN pruning in later implementations [V-abs].** Kirshanova-May-Wiemer and their code call it "Linear Length Pruning" and implement it alongside LP's NearestPlanes.
  - Reference: E. Kirshanova, A. May and F. Wiemer, "Parallel Implementation of BDD Enumeration for LWE", ACNS 2016, LNCS 9696, pp. 580-591, DOI 10.1007/978-3-319-39555-5_31, ePrint 2016/380.
  - The abstract says they parallelise BDD enumeration "using the Lindner-Peikert and Linear Length pruning strategies". The code makes Liu-Nguyen linear-length pruning the default.
  - Sources: [ePrint 2016/380](https://eprint.iacr.org/2016/380); [code README](https://github.com/rub-hgi/cvp-enum); [Crossref](https://api.crossref.org/works/10.1007/978-3-319-39555-5_31).
- **Lattice-estimator [V-abs].** The `PrimalHybrid` docs say that with guessing dimension zeta = 0 the function "essentially estimates the BDD strategy as given in [RSA:LiuNgu13]". The `babai` flag means "Insist on Babai's algorithm for finding close vectors". So LN13 remains the reference final-step model in the standard estimator. Source: [lattice-estimator docs](https://lattice-estimator.readthedocs.io/en/latest/_apidoc/estimator.lwe_primal/estimator.lwe_primal.PrimalHybrid.html).
- **Further experiments [V-meta].** R. Xu, S. L. Yeo, K. Fukushima, T. Takagi, H. Seo, S. Kiyomoto and M. Henricksen, "An Experimental Study of the BDD Approach for the Search LWE Problem", ACNS 2017, LNCS 10355, pp. 253-272, DOI 10.1007/978-3-319-61204-1_13. Abstract not retrievable; metadata via [OpenAlex](https://api.openalex.org/works/doi:10.1007/978-3-319-61204-1_13) and [Springer](https://link.springer.com/chapter/10.1007/978-3-319-61204-1_13).
- **Band pruning [V-abs].** Y. Aono, L. T. Phong and L. Wang, "Hardness Estimation of LWE via Band Pruning", IACR ePrint 2015/1026. It extends LP11, LN13 and Aono et al. 2013 with "a new bounding method named band pruning in lattice enumeration" for search-LWE. Source: [ePrint 2015/1026](https://eprint.iacr.org/2015/1026).

### Inferences
- LN13 pruning is axis (d): an absolute radius bound per level on the partial squared distance, depth-first, with success probability computed from the Gaussian error and repeated randomisation.
- VA-ANP's beam pruning ("accumulated distance minus best <= T*2*sigma^2") is a different shape: breadth-first and relative to the current best.
- Under a Gaussian error, LN-style per-level radii and VA-ANP's relative threshold both approximate "keep candidates whose likelihood is within a factor of the best". A reviewer will likely say VA-ANP is "pruned enumeration in breadth-first order". VA-ANP should benchmark against LN13 linear pruning (for example the KMW code) and not only against LP or fixed-size lists.

### Gaps
- I could not open the LN13 full text (Springer paywall). Two points therefore rest on secondary sources (Bischof et al.; KMW naming) plus memory:
  - the exact form of the bounding function (linear pruning R_k^2 proportional to k/n);
  - whether LN explicitly derive LP as enumeration with coefficient (box) bounds.
- I also did not open the full text of Xu et al. 2017 or the band-pruning PDF (ePrint PDFs returned 403).

## Q3. Klein's randomized nearest plane and Liu-Ling-Stehlé "Decoding by Sampling" (IEEE TIT 2011): are the choices per-node and target-dependent?

### Takeaway
Yes. Klein's algorithm and its LLS refinement choose the integer coefficient at each level at random. The probability is proportional to exp(-A * r_ii^2 * (c_i - x)^2), where r_ii = ||b*_i|| and c_i is the target-dependent centre at that node. This is a per-node, target-dependent, likelihood-weighted soft version of "keep planes whose extra squared distance is small relative to a sigma-like scale". LLS optimise the scale A and the number of samples K, and keep the closest of K samples. This is direct prior art for axis (b), in randomized form. MCMC follow-ups extend it.

### Cited Findings
- **LLS reference [V-full].**
  - Authors and title: S. Liu, C. Ling and D. Stehlé, "Decoding by Sampling: A Randomized Lattice Algorithm for Bounded Distance Decoding".
  - Venue: IEEE Trans. Inf. Theory 57(9):5933-5945, 2011, DOI 10.1109/TIT.2011.2162180, arXiv:1003.0064.
  - Sources: [arXiv](https://arxiv.org/abs/1003.0064); [Crossref](https://api.crossref.org/works/10.1109/TIT.2011.2162180).
- **Klein as LLS describe it.** Klein's algorithm is "a randomized version of Babai's nearest plane algorithm (i.e., SIC)". Its "core ... is randomized rounding". Source: [LLS, arXiv PDF](https://arxiv.org/pdf/1003.0064).
- **Per-level sampling distribution (Lemma 2 / Eq. 17).** The probability that x_i equals a given integer is at least proportional to exp(-A * r_ii^2 * ((y_i - sum_{j>i} r_ij x_j)/r_ii - x)^2).
  - The centre depends on the target y and on the already-fixed coordinates, so it is per node.
  - Klein's choice is A = log n / min_i r_ii^2.
  - LLS show this choice is not optimal and optimise the decoding radius.
  - Source: [LLS PDF](https://arxiv.org/pdf/1003.0064).
- **List behaviour.** LLS sample K candidates and keep the closest. They report that "near-ML performance is achieved by a moderate number of samples" for dimensions up to 32. Source: [arXiv abstract](https://arxiv.org/abs/1003.0064).
- **Klein's original paper [UNVERIFIED, page not opened].** P. N. Klein, "Finding the closest lattice vector when it's unusually close", SODA 2000, pp. 937-941. It is cited with these details in [LP11](https://web.eecs.umich.edu/~cpeikert/pubs/lwe-analysis.pdf) and [LLS](https://arxiv.org/pdf/1003.0064). LP's footnote says Klein "also can recurse on more than one plane per iteration" and "can also be derandomized".
- **MCMC follow-up [V-abs].** Z. Wang and C. Ling, "Lattice Gaussian Sampling by Markov Chain Monte Carlo: Bounded Distance Decoding and Trapdoor Sampling", IEEE TIT 65(6):3630-3645, 2019, DOI 10.1109/TIT.2019.2901497. It analyses BDD with independent Metropolis-Hastings-Klein, giving "a flexible trade-off between the decoding radius and complexity". Source: [OpenAlex record](https://api.openalex.org/works/doi:10.1109/tit.2019.2901497).

### Inferences
- VA-ANP's per-node rule keeps a plane if r_ii^2 * (c_i - x)^2 - (nearest plane's value) <= llr * 2*sigma^2. That is the deterministic, thresholded analogue of Klein/LLS sampling with A ~ 1/(2*sigma^2): keep the planes whose Klein weight is within e^{-llr} of the nearest plane's weight.
- This idea, choosing planes per node by target-dependent distance on a sigma scale, is therefore published in randomized form (Klein 2000, LLS 2011). Per-node deterministic thresholds are also published (Q6).
- The team's finding that the per-node rule adds nothing over plain 3-plane beam search with the same pruning is consistent with this. The accumulated-distance pruning already subsumes most of a per-node likelihood test.

### Gaps
- I did not find a paper that implements a derandomized, threshold version of Klein inside an LWE attack pipeline. I cannot rule one out.

## Q4. Discrete pruning (Aono-Nguyen EUROCRYPT 2017) and "Application of Discrete Pruned Enumeration in Solving BDD" (Symmetry 2023): what do they do?

### Takeaway
Aono-Nguyen generalise Schnorr's random sampling into "discrete pruning". Space is partitioned into cells indexed by integer tags. One enumerates the cells most likely to contain short vectors, ranked by expected length and ball-box intersection volumes. This is for SVP. Luan, Shi, Gu and Zheng (2023) port discrete pruning to BDD/CVP. They show that Babai's nearest plane and LP NearestPlanes are discrete pruned enumeration on special pruning sets. They report it beats both nearest planes and classical pruned enumeration on LWE and DSA-HNP instances. This is close prior art for "choose which plane combinations to visit by expected (likelihood) cost", with use in LWE attacks (e).

### Cited Findings
- **Aono-Nguyen reference [V-abs].** Y. Aono and P. Q. Nguyen, "Random Sampling Revisited: Lattice Enumeration with Discrete Pruning", EUROCRYPT 2017, LNCS 10211, DOI 10.1007/978-3-319-56614-6_3, ePrint 2017/155.
  - The abstract introduces "lattice enumeration with discrete pruning" as a generalisation of random sampling, based on partitions of n-dimensional space.
  - It is analysed under the Gaussian heuristic, using ball-box intersection volumes and parameter selection by enumerating integer points in an ellipsoid.
  - The abstract does not mention BDD/CVP.
  - Sources: [ePrint 2017/155](https://eprint.iacr.org/2017/155); [Crossref search result DOI](https://api.crossref.org/works/10.1007/978-3-319-56614-6_3).
- **Luan et al. reference [V-abs].** L. Luan, Y. Shi, C. Gu and Y. Zheng, "Application of Discrete Pruned Enumeration in Solving BDD", Symmetry 15(2):355, 2023, DOI 10.3390/sym15020355. Sources: [MDPI](https://www.mdpi.com/2073-8994/15/2/355); [Crossref](https://api.crossref.org/works/10.3390/sym15020355); [OpenAlex abstract](https://api.openalex.org/works/doi:10.3390/sym15020355).
- **What the Luan et al. abstract says.**
  - They "transfer the basic definition involved in discrete pruning technique from SVP to CVP" and give the algorithm.
  - They "interpret the classical CVP algorithms, including Babai's nearest plane and Lindner-Peikert nearest planes, which can be regarded as discrete pruned enumeration on some special pruning sets".
  - They propose "three probability models" for runtime and cost analysis.
  - They apply the method to LWE-based cryptosystems and DSA with partially known nonces. They report higher efficiency than "the nearest plane(s) algorithms and the lattice enumeration with classical pruning strategies".
  - Source: [OpenAlex abstract](https://api.openalex.org/works/doi:10.3390/sym15020355).

### Inferences
- Discrete pruning for BDD selects a set of plane-index combinations (cells or tags) globally by expected squared distance. That is a likelihood-ranked list of candidate plane combinations, conceptually the same objective as VA-ANP's likelihood-pruned list.
- If Luan et al. rank cells by expected distance from the target's Babai coordinates, as Aono-Nguyen do for SVP, the selection uses the per-level ||b*_i|| geometry but not the per-node realised distances. That would make it closer to (a) plus a global (c) than to (b). This is an inference: I could not open the full text.
- A VA-ANP paper must cite Luan et al. 2023 and should ideally compare against it, because it already claims to beat LP and classical pruning on LWE.

### Gaps
- The full text of Luan et al. was blocked (403 on MDPI and ResearchGate). I could not verify two points:
  - the exact tag/cell selection rule and whether it uses the realised target offsets;
  - the concrete LWE parameters and speedups.
- I did not verify "Quantum Lattice Enumeration and Tweaking Discrete Pruning" (Aono-Nguyen-Shen, ASIACRYPT 2018, [Springer link](https://link.springer.com/chapter/10.1007/978-3-030-03326-2_14)). I saw it only in search results.

## Q5. Extreme pruning (Gama-Nguyen-Regev 2010) applied to BDD/CVP

### Takeaway
GNR introduced per-level bounding functions (radius bounds on projected lengths) and "extreme" pruning. Extreme pruning means very low per-tree success probability compensated by rerandomising the basis and repeating. GNR targeted SVP. LN13 applied it to BDD in LWE, DSA and GGH. KMW 2016 parallelised it. This is the reference point for (d) and (e).

### Cited Findings
- **GNR reference [V-meta].** N. Gama, P. Q. Nguyen and O. Regev, "Lattice Enumeration Using Extreme Pruning", EUROCRYPT 2010, LNCS 6110, DOI 10.1007/978-3-642-13190-5_13. Source: [Crossref](https://api.crossref.org/works/10.1007/978-3-642-13190-5_13).
- **GNR pruning model.** As quoted in search results from the GNR text, "the pruning is determined by an arbitrary bounding function, which provides for each level of the tree an upper bound on the distance of nodes that should be considered" ([academia.edu copy](https://www.academia.edu/8322651/Lattice_Enumeration_Using_Extreme_Pruning); I did not open it myself).
- **Application to BDD.** LN13 explicitly apply "Gama-Nguyen-Regev's extreme pruning" to BDD ([Springer page](https://link.springer.com/chapter/10.1007/978-3-642-36095-4_19)). KMW 2016 parallelise LP and LN pruning for LWE. They report near-linear speedup, practical attacks on "standard-size LWE parameters", and outperformance of BKW-type algorithms for small noise ([ePrint 2016/380](https://eprint.iacr.org/2016/380)).
- **LP noted GNR.** LP cite GNR's "Extreme Enum" only as a possible SVP/BKZ subroutine and did not use it for decoding ([LP11, Sec. 5](https://web.eecs.umich.edu/~cpeikert/pubs/lwe-analysis.pdf)).

### Inferences
- VA-ANP's cap plus threshold is a single-pass, breadth-first scheme. It does not use extreme pruning with rerandomisation.
- "Many cheap low-success decodings over rerandomised bases" (GNR/LN) is the main competitor for a fixed node budget. A fair comparison should include it.

### Gaps
- I did not open the GNR full text, so the GNR details above are from secondary quotes and memory. I found no 2020-2026 paper that revisits extreme pruning specifically for BDD.

## Q6. Communications-side prior art: threshold SE sphere decoding (2014), probabilistic tree pruning (Shim-Kang), statistical pruning, K-best with adaptive K or LLR thresholds, T-algorithm and M-algorithm

### Takeaway
Every pruning ingredient of VA-ANP has a direct MIMO or trellis-decoding precedent:
- Noise-statistics thresholds on Schnorr-Euchner children (TSE 2014; Shim-Kang 2008; Gowaikar-Hassibi 2007).
- Breadth-first lists with a fixed cap (M-algorithm 1984; K-best, e.g. Guo-Nilsson 2006).
- Breadth-first lists pruned relative to the best metric (T-algorithm, Simmons 1990).
- K-best with per-layer threshold = smallest PED + noise-dependent margin (Mao-Cheng-Xiang 2013).
- Adaptive pruning thresholds inside K-best (Shen-Eltawil 2010).

The "likelihood-pruned list saves 5-7x nodes versus fixed-size list" result is the classical T-algorithm vs M-algorithm finding, restated for BDD.

### Cited Findings
- **TSE (threshold-based SE sphere decoding), the original publication [V-abs].**
  - M. Karthikeyan and D. Saraswady, "Sphere decoding using threshold based Schnorr-Euchner enumeration in MIMO system".
  - Venue: Int. Conf. on Recent Trends in Information Technology (ICRTIT), Chennai, Apr. 2014, pp. 1-4, DOI 10.1109/ICRTIT.2014.6996088.
  - The abstract describes "the probabilistic threshold for SE enumeration to remove the nodes which are most unlikely to be an ML solution". The threshold "is chosen using the pruning probability based on noise statistics".
  - Sources: [OpenAlex abstract](https://api.openalex.org/works/doi:10.1109/ICRTIT.2014.6996088); [Semantic Scholar metadata](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/ICRTIT.2014.6996088?fields=title,authors,venue,year); [IEEE Xplore](https://ieeexplore.ieee.org/document/6996088) (the page did not render for me).
- **Shim-Kang [V-abs].**
  - B. Shim and I. Kang, "Sphere Decoding With a Probabilistic Tree Pruning", IEEE Trans. Signal Process. 56(10):4867-4878, Oct. 2008, DOI 10.1109/TSP.2008.923808.
  - They add "a probabilistic noise constraint on top of the sphere constraint", so "branches unlikely to be survived are removed in the early stage". The trade-off is set by "a single parameter, so-called pruning probability".
  - The conference version is "Radius-adaptive sphere decoding via probabilistic tree pruning", SPAWC 2007.
  - Sources: [OpenAlex abstract](https://api.openalex.org/works/doi:10.1109/TSP.2008.923808); [Korea Univ. record](https://scholar.korea.ac.kr/handle/2021.sw.korea/122602); [Crossref](https://api.crossref.org/works/10.1109/TSP.2008.923808).
- **Gowaikar-Hassibi [V-abs].** R. Gowaikar and B. Hassibi, "Statistical Pruning for Near-Maximum Likelihood Decoding", IEEE Trans. Signal Process. 55(6), 2007, DOI 10.1109/TSP.2006.890912. They "statistically prune the search space to a subset that, with high probability, contains the optimal solution", with error bounds and complexity analysis. Source: [OpenAlex abstract](https://api.openalex.org/works/doi:10.1109/tsp.2006.890912).
- **T-algorithm [V-abs].**
  - S. J. Simmons, "Breadth-first trellis decoding with adaptive effort", IEEE Trans. Commun. 38(1), 1990, DOI 10.1109/26.46522.
  - The algorithm "maintains a variable number of paths as its computation adapts to the channel noise actually encountered".
  - It has error-rate vs average-complexity behaviour "much superior to the Viterbi algorithm" and "improves on the M-algorithm".
  - Source: [OpenAlex abstract](https://api.openalex.org/works/doi:10.1109/26.46522).
- **M-algorithm survey [V-meta].** J. B. Anderson and S. Mohan, "Sequential Coding Algorithms: A Survey and Cost Analysis", IEEE Trans. Commun. 32(2), 1984, DOI 10.1109/TCOM.1984.1096023. This is the standard reference for the fixed-size breadth-first M-algorithm. Source: [Crossref](https://api.crossref.org/works/10.1109/TCOM.1984.1096023).
- **K-best [V-meta].** Z. Guo and P. Nilsson, "Algorithm and implementation of the K-best sphere decoding for MIMO detection", IEEE JSAC 24(3), 2006, DOI 10.1109/JSAC.2005.862402. Source: [Crossref](https://api.crossref.org/works/10.1109/JSAC.2005.862402).
- **K-best with a noise-based threshold relative to the best PED per layer [V-abs].**
  - X. Mao, Y. Cheng and H. Xiang, "Partial Noise Value Aided Reduced K-Best Sphere Decoding", IEEE VTC-Fall 2013, DOI 10.1109/VTCFall.2013.6692345.
  - "By adding a parameter determined by both noise and quality of service (QoS) to the smallest PED in each searching layer, a tighter ... threshold can be calculated for this layer."
  - The abstract also says "statistical characteristic of noise has been well explored to generate thresholds". They report about 90% complexity reduction.
  - Source: [OpenAlex abstract](https://api.openalex.org/works/doi:10.1109/vtcfall.2013.6692345).
- **Adaptive pruning threshold in K-best [V-abs].** C.-A. Shen and A. M. Eltawil, "A Radius Adaptive K-Best Decoder With Early Termination: Algorithm and VLSI Architecture", IEEE TCAS-I 57(9):2476-2486, 2010, DOI 10.1109/TCSI.2010.2043017. It combines radius shrinking with K-best, "branch pruning and adaptively updated pruning threshold", and needs "much smaller K". Source: [OpenAlex abstract](https://api.openalex.org/works/doi:10.1109/tcsi.2010.2043017).
- **List sphere decoding [V-meta].** B. M. Hochwald and S. ten Brink, "Achieving near-capacity on a multiple-antenna channel", IEEE Trans. Commun. 51(3):389-399, 2003, DOI 10.1109/TCOMM.2003.809789. This is the standard reference for list sphere decoding with LLR output. Sources: [Crossref](https://api.crossref.org/works/10.1109/TCOMM.2003.809789); [OpenAlex](https://api.openalex.org/works/doi:10.1109/TCOMM.2003.809789).
- **Other adaptive-K and LLR-threshold K-best work (search snippets only, not opened) [UNVERIFIED].**
  - Dynamic K from the gap between best and second-best PED per level (Fan et al. 2014).
  - Adaptive K from the ratio of the two smallest metrics (Chang, Liao and Chang, NCTU).
  - An a-priori LLR threshold for K-best (VTC 2008, Southampton, [PDF link](https://www.southampton.ac.uk/~sqc/listP/vtc08s-03-14-01.pdf)).
  - Adaptive-K K-best for DVB-T2 (El-Banna et al., ISWCS 2013, [VDE](https://www.vde-verlag.de/proceedings-en/453529097.html)).
- **Schnorr-Euchner enumeration [V-meta].** C. P. Schnorr and M. Euchner, "Lattice basis reduction: Improved practical algorithms and solving subset sum problems", Math. Programming 66, 1994, DOI 10.1007/BF01581144. Source: [Crossref](https://api.crossref.org/works/10.1007/BF01581144).

### Inferences
- **(c) relative-to-best likelihood pruning of a breadth-first list** = the T-algorithm (Simmons 1990) and Mao-Cheng-Xiang 2013. A cap on list size = the M-algorithm / K-best. Combining a T-threshold with an M/K cap is standard engineering practice in MIMO detectors, but I did not open a specific "M+T hybrid" paper (see Gaps).
- **(b) per-node noise-scaled threshold on SE children** = TSE 2014 and Shim-Kang 2008. A "third plane matters at hard settings" corresponds to the standard observation that the number of children kept per node must grow at low SNR.
- **(d)** = Fincke-Pohst / Schnorr-Euchner sphere decoding with per-level probabilistic radii (Gowaikar-Hassibi; Shim-Kang).
- None of these communications papers targets LWE or BDD in cryptanalysis (axis (e)). That application gap is the only place the team's work could be new, and it would be an application or benchmark, not a new decoder.

### Gaps
- I could not open IEEE Xplore pages or full texts, so the exact threshold formulas (TSE, Shim-Kang, Mao et al.) are known only from abstracts.
- I did not find or verify a canonical "M-T hybrid" reference, although Simmons' abstract compares against the M-algorithm.
- I did not verify the Fan et al. 2014 dynamic K-best or the VTC 2008 a-priori LLR K-best papers.

## Q7. 2020-2026 papers on list decoding, beam search, nearest-colattice or nearest-planes improvements for BDD in lattice cryptanalysis

### Takeaway
Recent crypto work on the final BDD step has gone in other directions:
- precomputation-friendly approximate CVP (nearest-colattice, 2020);
- approximate Voronoi cells / CVPP (2019);
- batched or projected Babai on GPUs for hybrid attacks (2025);
- discrete-pruning BDD (2023);
- batch-BDD trade-offs (2019).

I found no 2020-2026 cryptanalysis paper that proposes a beam-search or K-best/T-algorithm breadth-first decoder with likelihood-relative pruning as the BDD step of the primal LWE attack. This is a search-based absence, not a proof.

### Cited Findings
- **Nearest-colattice [V-abs].**
  - T. Espitau and P. Kirchner, "The nearest-colattice algorithm: Time-approximation tradeoff for approx-CVP".
  - Venue: ANTS XIV 2020, Open Book Series 4, p. 251, DOI 10.2140/obs.2020.4.251, arXiv:2006.05660.
  - The abstract describes a "hierarchy of polynomial time algorithms solving approximate variants of the closest vector problem". It reaches the HSVP-like tradeoff and, unlike Kannan embedding, "allows the use of precomputations" and batch CVP.
  - Sources: [OpenAlex abstract](https://api.openalex.org/works/doi:10.2140/obs.2020.4.251); [arXiv](https://arxiv.org/abs/2006.05660v2).
- **Batched Babai on GPUs [V-abs].** L. N. Pulles and P. Vié, "Accelerating the Primal Hybrid Attack against Sparse LWE using GPUs", IACR ePrint 2025/1990 (preprint). It uses "a batched variant of Babai's Nearest Plane algorithm", a dimension reduction for the BDD instance, and GPU BLASter. It reports better success than Cool&Cruel on most benchmark instances. Source: [ePrint 2025/1990](https://eprint.iacr.org/2025/1990).
- **Batch-BDD trade-offs [V-abs].** M. R. Albrecht, B. R. Curtis and T. Wunderer, "Exploring Trade-offs in Batch Bounded Distance Decoding", SAC 2019, ePrint 2019/1122. It guesses components and then decodes. It beats a hybrid variant for some Round5 and NTRU LPrime parameters in the enumeration setting, but not in the sieving setting. Source: [ePrint 2019/1122](https://eprint.iacr.org/2019/1122).
- **Approximate Voronoi cells [V-meta].** E. Doulgerakis, T. Laarhoven and B. de Weger, "Finding Closest Lattice Vectors Using Approximate Voronoi Cells", PQCrypto 2019, LNCS 11505, pp. 3-22, DOI 10.1007/978-3-030-25510-7_1. Source: [Crossref](https://api.crossref.org/works/10.1007/978-3-030-25510-7_1).
- **Hybrid attack origin [V-meta].** N. Howgrave-Graham, "A Hybrid Lattice-Reduction and Meet-in-the-Middle Attack Against NTRU", CRYPTO 2007, LNCS 4622, pp. 150-169, DOI 10.1007/978-3-540-74143-5_9. It uses Babai's nearest plane as the decoding oracle and is the reference behind the estimator's `babai=True` hybrid. Sources: [Crossref](https://api.crossref.org/works/10.1007/978-3-540-74143-5_9); [lattice-estimator docs](https://lattice-estimator.readthedocs.io/en/latest/_apidoc/estimator.lwe_primal/estimator.lwe_primal.PrimalHybrid.html).
- **Meet-LWE / Babai papers [UNVERIFIED, search snippets only].**
  - ePrint 2022/1473, "A Hybrid of Lattice-reduction and Meet-LWE via Near-Collision on Babai's Plane" ([PDF link](https://eprint.iacr.org/2022/1473.pdf)).
  - ePrint 2024/824, "Improved Meet-LWE Attack via Ternary Trees" ([PDF link](https://eprint.iacr.org/2024/824.pdf)).
  - Both use Babai's nearest plane as the BDD step inside hybrid or MitM attacks, not list or beam decoders.
- **The "primal BDD" final step in ML-attack benchmarks.** SALSA notes that BDD "can be solved by Babai's Nearest Plane algorithm or pruned enumeration" (snippet only, [arXiv 2207.04785](https://arxiv.org/pdf/2207.04785)). The 2024 "Benchmarking Attacks on Learning with Errors" lists BDD and primal hybrid as future work (snippet only, [arXiv 2408.00882](https://arxiv.org/pdf/2408.00882)). Both are [UNVERIFIED].

### Inferences
- The most recent decoder-side novelty in crypto (Luan et al. 2023, discrete pruning) already claims to beat LP and classical pruning for LWE.
- The engineering trend since then (Pulles-Vié 2025) favours batched plain Babai on GPUs plus guessing, not wider per-instance lists.
- A VA-ANP contribution should be framed as "T-algorithm / threshold K-best style breadth-first list decoding as the BDD step of the primal LWE attack, with a fair node-count comparison against LP NearestPlanes, LN13 linear/extreme pruning, and discrete pruning". It should cite the communications sources as the origin of the technique.

### Gaps
- My search coverage of 2020-2026 ePrint was keyword-based (about 6 queries). I did not verify any ePrint papers from 2026, and Google Scholar and dblp could not be queried (dblp returned a bot-protection page).
- I did not verify "On Bounded Distance Decoding with Predicate" (Albrecht-Heninger, EUROCRYPT 2021). It is relevant as an enumeration/sieving final step with a predicate.

## Q8. Synthesis: which VA-ANP ideas, and close variants, are already published?

### Takeaway
Every algorithmic ingredient of VA-ANP is published:
- (a) per-level plane counts from ||b*_i|| and sigma: LP 2011.
- (b) per-node, target-dependent, sigma-scaled plane choice: Klein 2000 and LLS 2011 in randomized form; TSE 2014 and Shim-Kang 2008 as deterministic thresholds.
- (c) likelihood/threshold pruning of a breadth-first list, plus a cap: T-algorithm 1990, M-algorithm/K-best, Mao-Cheng-Xiang 2013, Shen-Eltawil 2010.
- (d) sphere-radius pruning: SE 1994, GNR 2010, LN 2013, Gowaikar-Hassibi 2007.
- (e) final step of the LWE attack: LP 2011, LN 2013, KMW 2016, Luan et al. 2023, lattice-estimator.

The defensible novelty is narrow and empirical. Within lattice cryptanalysis, I found no paper benchmarking a breadth-first, relative-likelihood-pruned (T-algorithm style) beam decoder against LP/LN/discrete pruning as the primal-attack BDD step.

### Cited Findings
- **Closeness matrix.** Y = does it; ~ = partially or analogous; N = no. Sources are as cited in Q1-Q7.

| Work | (a) per-level from b*_i, sigma | (b) per-node target-dependent | (c) BFS list, likelihood/threshold pruning | (d) sphere radius pruning | (e) LWE primal final step |
|---|---|---|---|---|---|
| Babai 1986 nearest plane | N (1 plane) | ~ (rounds to the nearest, target-dependent) | N | N | Y (as baseline) |
| Schnorr-Euchner 1994 enum | N | Y (zig-zag order by distance) | N (depth-first) | Y | ~ |
| Klein 2000 / LLS 2011 ([arXiv](https://arxiv.org/abs/1003.0064)) | ~ (A scale from min r_ii) | Y (randomized, prob ~ exp(-A r_ii^2 (c-x)^2)) | ~ (K samples, keep best) | N | N (MIMO; crypto via LP footnote) |
| Lindner-Peikert 2011 ([PDF](https://web.eecs.umich.edu/~cpeikert/pubs/lwe-analysis.pdf)) | Y (d_i from b*_i and s) | N | N | N (box) | Y |
| GNR 2010 extreme pruning | ~ (bounding function per level) | N | N | Y | via LN13 |
| Liu-Nguyen 2013 ([Springer](https://link.springer.com/chapter/10.1007/978-3-642-36095-4_19)) | ~ | N | N | Y (linear/extreme) | Y |
| KMW 2016 ([ePrint](https://eprint.iacr.org/2016/380)) | Y (LP) | N | N | Y (LN) | Y |
| Aono-Nguyen 2017 discrete pruning ([ePrint](https://eprint.iacr.org/2017/155)) | ~ (cells ranked by expected length) | N (SVP) | ~ (global ranked cell list) | ~ | N |
| Luan et al. 2023 ([MDPI](https://www.mdpi.com/2073-8994/15/2/355)) | ~ | unknown | ~ (ranked cell list, probability models) | ~ | Y (LWE, DSA) |
| Gowaikar-Hassibi 2007 | Y (statistical per-level radii) | ~ | N | Y | N |
| Shim-Kang 2008 | Y (noise-probabilistic per-level constraint) | Y | N | Y | N |
| TSE, Karthikeyan-Saraswady 2014 | ~ | Y (noise-based threshold on SE children) | N | Y | N |
| Simmons 1990 T-algorithm | N | N | Y (keep paths within T of best) | N | N |
| Anderson-Mohan 1984 M-algorithm / Guo-Nilsson 2006 K-best | N | N | ~ (fixed-size list) | N | N |
| Mao-Cheng-Xiang 2013 | Y (noise-based per layer) | N | Y (threshold = min PED + noise margin) | ~ | N |
| Shen-Eltawil 2010 | N | N | Y (adaptive pruning threshold in K-best) | Y | N |
| Wang-Ling 2019 MCMC BDD | ~ | Y | N | N | N |
| Espitau-Kirchner 2020 nearest-colattice | N | N | N | N | ~ (approx-CVP, batch, signatures) |
| Pulles-Vié 2025 ([ePrint](https://eprint.iacr.org/2025/1990)) | N | N | N (batched Babai) | N | Y (hybrid) |

- **The team's three empirical findings map onto known results:**
  - (i) Likelihood pruning beats a fixed-size list (5-7x fewer nodes). This is the T-algorithm vs M-algorithm result; Simmons reports that the T-algorithm "improves on the M-algorithm" ([OpenAlex](https://api.openalex.org/works/doi:10.1109/26.46522)).
  - (ii) A third plane matters at hard settings. This matches LP's rationale for d_i > 1 when ||b*_i|| is small relative to s ([LP11](https://web.eecs.umich.edu/~cpeikert/pubs/lwe-analysis.pdf)).
  - (iii) The per-node plane rule adds nothing over plain 3-plane beam search with the same pruning. This is consistent with accumulated-metric pruning (T-algorithm) subsuming per-node likelihood thresholds (Klein/TSE). It is the team's own result; I found no paper that states this ablation for BDD.

### Inferences
- **Claims to avoid:**
  - "new plane-selection rule from ||b*_i|| and sigma" (LP 2011);
  - "new per-node likelihood/LLR plane selection" (Klein/LLS; TSE; Shim-Kang);
  - "new likelihood-pruned breadth-first list decoder" (T-algorithm; threshold K-best);
  - "first to view nearest planes as pruned search" (LN 2013; Luan et al. 2023).
- **Claims that look defensible if stated carefully:**
  - a fair, node-count-matched empirical comparison in the LWE primal-attack setting between LP NearestPlanes, LN13 pruned enumeration, discrete pruning and a T-algorithm-style beam;
  - the negative ablation result that per-node plane rules add nothing over relative-threshold beam pruning;
  - possibly a success-probability or cost model for relative-threshold beams in the GSA/BKZ profile setting, if none exists.
  - All of these require citing the communications precedents.

### Gaps
- The full texts of LN13, Luan et al. 2023, GNR 2010, Xu et al. 2017 and the communications threshold papers were not accessible. Fine-grained details (exact bounding functions, cell-selection rules, threshold formulas) are therefore abstract-level or secondary-source.
- I could not search Google Scholar or dblp directly. A cryptanalysis paper using "K-best" or "beam" decoding for LWE under a different name (for example "list Babai" or "stack decoding") may exist and was not found.
