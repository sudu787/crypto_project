# BDD decoding study for toy LWE

This repo tests how well decoding attacks on LWE are predicted, using toy parameters only. Nothing here makes a security claim about ML-KEM or Kyber.

## Main result
Retrying the decoding attack on re-randomised bases is **not** independent per instance. That independence is assumed by Liu–Nguyen 2013, Wunderer 2019 and the lattice estimator's `amplify()`.

For BKZ bases, conditioning on each instance's own error norm ‖e‖ explains the dependence. This was confirmed by rule R8, which was fixed before the run and tested on fresh instances: the model was off in 0 of 16 cells, against 12 of 16 for the independent model.

The full write-up, including the tests that failed (R5, R6, R7 and R9 on LLL), is in [Retry_study_summary.md](Retry_study_summary.md).

## Where things are
| File(s) | Contents |
|---|---|
| `Retry_study_summary.md` | Retry study: results, prior work, what is new and what is not |
| `Decoding_study_summary.md` | Decoding study; the estimator gap turned out to be under-reduced BKZ |
| `BDD_decoding_study.ipynb` | Decoding study notebook |
| `retry_study.py`, `retry_exact.py`, `retry_impact.py` | Retry experiments; pre-registered rules in the docstrings |
| `Retry_theory.md`, `theory_check.py` | Proofs (P1–P3) and their numerical checks |
| `retry_cost.py` | Attempts needed for 99% success and the give-up rule |
| `retry_lll.py` | LLL mechanism and scrambled re-randomisation (rule R11) |
| `retry_enum.py` | Pruned enumeration retries (rule R12) |
| `retry_scale.py` | Scale-up to n = 120 (Babai) and n = 150 (enumeration) (rule R10) |
| `lwe_challenge.py`, `lwe_challenge/` | TU Darmstadt LWE challenge instances (rule R13) |
| `estimator_fixed_error.patch`, `retry_impact2.py` | Lattice-estimator option `repetition_model="fixed_error"` and its effect |
| `toy_lwe_test.py`, `toy_lwe_gpu.py`, `decoding_study.py` | Toy LWE instances, BKZ reduction and the GPU decoders |
| `CVP_VA_ANP_*.ipynb`, `va_anp_v2.py`, `stress_test_*.py` | VA-ANP decoder experiments (not novel; it fails its tests at scale) |
| `AS_VA_ANP_colab.ipynb` | AS-VA-ANP code split into Colab cells, plus check cells |
| `research_notes/`, `reports/` | Literature checks and the novelty analysis |
| `graphify-out/graph.html` | Knowledge graph of the project; open it in a browser |
| `*_log.txt`, `*.json` | Raw experiment logs and results |

## Not included
The Liu–Nguyen paper is not included because it is copyrighted. Its reference is "Solving BDD by Enumeration: An Update", CT-RSA 2013, LNCS 7779, pp. 293–309.
