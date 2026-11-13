// Builds Retry_study_deck.pptx (10 slides). Run: NODE_PATH=<dir with pptxgenjs> node make_deck.js
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("C:/Users/sudu/AppData/Local/Claude-Data/claude_pzs8sxrjxfjjc/local-agent-mode-sessions/skills-plugin/599e8237-82ee-4351-8e06-f35c399d2682/a6cbf77e-f06a-4646-9647-182540a510c5/skills/pptx/scripts/apply_theme.js");

const OUT = "D:/ABHILASH CRYPTO PROJECT/Retry_study_deck.pptx";
const THEME = {
  name: "Lattice Retry",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1A1A2E", lt1: "FFFFFF", dk2: "14213D", lt2: "EEF1F6",
    accent1: "F2A541", accent2: "2A9D8F", accent3: "E76F51",
    accent4: "8D99AE", accent5: "264653", accent6: "E9C46A",
    hlink: "2A9D8F", folHlink: "8D99AE",
  },
};
const H = THEME.colors; // hex, for hex-only options (chart colors, grid lines)
const TEAL_TINT = "E3F2F0", CORAL_TINT = "FBE9E4", FAIL_TEXT = "B5462B";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Repeated lattice decoding attempts are not independent";
const C = pres.SchemeColor;
const FOOT = "Toy parameters only. Nothing here is a claim about ML-KEM security.";

pres.defineSlideMaster({
  title: "Title dark",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.3, w: 5.6, h: 1.9, fontSize: 34, bold: true, color: C.background1, valign: "bottom", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.35, w: 5.6, h: 1.3, fontSize: 16, color: C.background2, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "Content",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.28, w: 9, h: 0.75, fontSize: 26, bold: true, color: C.text2, valign: "middle", margin: 0, align: "left" }, text: "" } },
    { text: { text: FOOT, options: { x: 0.5, y: 5.2, w: 7.5, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: C.accent4, align: "right" },
});

// ---------- helpers ----------
let n = 0;
const id = (s) => `${s}_${++n}`;
function content(section, title, notes) {
  const s = pres.addSlide({ masterName: "Content", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}
function card(s, x, y, w, h, fill) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill || C.background2 }, line: { type: "none" }, rectRadius: 0.08, objectName: id("card") });
}
function badge(s, x, y, label, fill, d = 0.42) {
  s.addText(label, { x, y, w: d, h: d, shape: pres.shapes.OVAL, fill: { color: fill }, color: C.background1, bold: true, fontSize: 13, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: id("badge") });
}
function text(s, t, o) {
  s.addText(t, Object.assign({ isTextBox: true, margin: 0, fontSize: 14, color: C.text1, valign: "top", objectName: id("text") }, o));
}
function stat(s, x, y, w, big, label, color, size = 32) {
  text(s, big, { x, y, w, h: 0.65, fontSize: size, bold: true, color, fontFace: THEME.headFontFace, valign: "bottom" });
  text(s, label, { x, y: y + 0.72, w, h: 0.7, fontSize: 12, color: C.text1 });
}
function bullets(items, size = 14) {
  return items.map((it, i) => ({ text: it, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6, fontSize: size } }));
}
function chartOpts(extra) {
  return Object.assign({
    catAxisLabelColor: H.dk1, valAxisLabelColor: H.accent4,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
    dataLabelFontFace: "+mn-lt", dataLabelFontSize: 10, dataLabelColor: H.dk1,
    legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: H.dk1,
    titleFontFace: "+mn-lt", titleFontSize: 12, titleColor: H.dk1,
    valGridLine: { color: "E3E7EE", size: 0.5 }, catGridLine: { style: "none" },
    valAxisLineShow: false, catAxisLineShow: true,
  }, extra);
}
function table(s, rows, o, failCol) {
  const tr = rows.map((r, i) => r.map((c, j) => ({ text: c, options: i === 0
    ? { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 12 }
    : { color: j === failCol ? FAIL_TEXT : C.text1, bold: j === 2, fill: { color: i % 2 ? C.background1 : C.background2 }, fontSize: 12 } })));
  s.addTable(tr, Object.assign({ border: { type: "none" }, align: "left", valign: "middle", margin: [0, 0.08, 0, 0.08] }, o));
}

// ---------- 1. Title ----------
pres.addSection({ title: "Introduction" });
{
  const s = pres.addSlide({ masterName: "Title dark", sectionTitle: "Introduction" });
  s.addText("Repeated lattice decoding attempts are not independent", { placeholder: "title" });
  s.addText("A pre-registered study on toy LWE: measurements, proofs and a lattice-estimator patch\nCrypto research project · November 2026", { placeholder: "body" });
  for (let r = 0; r < 6; r++) for (let c = 0; c < 5; c++) {
    s.addShape(pres.shapes.OVAL, { x: 6.75 + c * 0.6 + (r % 2) * 0.3, y: 0.75 + r * 0.7, w: 0.13, h: 0.13, fill: { color: C.accent4 }, line: { type: "none" }, objectName: id("dot") });
  }
  s.addShape(pres.shapes.OVAL, { x: 8.23, y: 2.83, w: 0.17, h: 0.17, fill: { color: C.accent2 }, line: { type: "none" }, objectName: "nearest_point" });
  s.addShape(pres.shapes.OVAL, { x: 8.45, y: 2.55, w: 0.17, h: 0.17, fill: { color: C.accent1 }, line: { type: "none" }, objectName: "target_point" });
  s.addShape(pres.shapes.LINE, { x: 8.32, y: 2.64, w: 0.18, h: 0.27, line: { color: C.accent1, width: 1.5, dashType: "dash" }, flipH: true, objectName: "error_vector" });
  s.addNotes("We ask whether the lattice estimator is right to treat repeated decoding attempts on one LWE instance as independent coin flips. It is not, and we can say exactly why and what it costs.");
}

// ---------- 2. Problem ----------
{
  const s = content("Introduction", "The problem: retries are assumed independent",
    "The primal attack on LWE ends with a decoding step. If it fails, the attacker re-randomises the basis and tries again. The estimator, Liu-Nguyen 2013 and Wunderer 2019 all count retries as independent trials with one success probability p. But on one instance the error vector never changes, so that assumption is questionable.");
  card(s, 0.5, 1.3, 4.35, 3.65);
  badge(s, 0.75, 1.5, "?", C.accent3);
  text(s, "What attack estimates assume", { x: 1.3, y: 1.52, w: 3.4, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
  text(s, bullets(["The attack decodes t = As + e against a reduced basis; on failure it re-randomises and retries.", "Every retry succeeds with the same p, independently.", "Attempts for 99% = log 0.01 / log(1 − p)."], 13), { x: 0.75, y: 2.1, w: 3.9, h: 2.7 });
  card(s, 5.15, 1.3, 4.35, 3.65, TEAL_TINT);
  badge(s, 5.4, 1.5, "!", C.accent2);
  text(s, "What actually happens", { x: 5.95, y: 1.52, w: 3.4, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
  text(s, bullets(["On one instance the error e never changes; only its direction relative to the basis does.", "Short ‖e‖: easy on every basis. Long ‖e‖: hard on every basis.", "So successes cluster by instance, and some instances are never solved."], 13), { x: 5.4, y: 2.1, w: 3.9, h: 2.7 });
}

// ---------- 3. What we did ----------
pres.addSection({ title: "Method" });
{
  const s = content("Method", "What we did",
    "The project had three phases. The first two gave honest nulls: the VA-ANP decoder was not novel, and the estimator's single-attempt formula turned out to be right once our BKZ bases were properly reduced. The third phase is the retry-dependence study. Every model test was written into a script before its bases were reduced.");
  const phases = [
    ["1", C.accent4, "VA-ANP decoder", "Not novel; failed at scale. Dropped."],
    ["2", C.accent4, "Decoding prediction", "Estimator gap came from under-reduced BKZ. Null."],
    ["3", C.accent2, "Retry dependence", "The new result: measured, modelled, proven, tested."],
  ];
  phases.forEach(([num, col, head, body], i) => {
    const y = 1.3 + i * 1.25;
    card(s, 0.5, y, 4.6, 1.1, i === 2 ? TEAL_TINT : C.background2);
    badge(s, 0.7, y + 0.3, num, col, 0.5);
    text(s, head, { x: 1.4, y: y + 0.15, w: 3.5, h: 0.35, fontSize: 15, bold: true, color: C.text2 });
    text(s, body, { x: 1.4, y: y + 0.55, w: 3.5, h: 0.45, fontSize: 12 });
  });
  stat(s, 5.6, 1.25, 3.9, "~20,000", "LLL/BKZ-reduced lattice bases (BKZ up to block size 40, dimension up to 300), on WSL with fplll.", C.text2, 30);
  stat(s, 5.6, 2.5, 3.9, "9 rules", "Pass/fail criteria fixed in advance (R5–R13), each tested on fresh instances. All results reported.", C.accent2, 30);
  stat(s, 5.6, 3.75, 3.9, "GPU", "Exact Babai success computed on an RTX A1000: 200,000 random directions per basis.", C.accent1, 30);
}

// ---------- 4. Main result ----------
pres.addSection({ title: "Results" });
{
  const s = content("Results", "Result: the error norm explains the dependence",
    "On 2,048 fresh BKZ bases (rule R8), the exact fixed-norm law, which has no fitted parameters, predicted the spread of success counts within 3 to 6 percent. The estimator's independent model underestimates it by a factor of 2 to 3. Independence itself was rejected in every setting, p at most 4e-4.");
  const L = ["BKZ-20 n=95 η=2", "BKZ-20 n=95 η=3", "BKZ-10 n=85 η=2", "BKZ-10 n=85 η=3"];
  s.addChart(pres.charts.BAR, [
    { name: "Measured", labels: L, values: [23.19, 3.94, 39.79, 12.39] },
    { name: "Exact law (ours)", labels: L, values: [22.56, 3.69, 38.14, 11.79] },
    { name: "Independent (estimator)", labels: L, values: [10.06, 2.25, 14.41, 5.55] },
  ], chartOpts({ x: 0.4, y: 1.2, w: 6.0, h: 3.85, barDir: "col", barGrouping: "clustered", chartColors: [H.dk2, H.accent2, H.accent3], showLegend: true, legendPos: "b", valAxisMinVal: 0, showTitle: true, title: "Variance of success counts per instance, 64 attempts (R8, fresh bases)", objectName: "r8_chart" }));
  stat(s, 6.8, 1.25, 2.7, "0 of 16", "Cells off for our exact law.", C.accent2);
  stat(s, 6.8, 2.5, 2.7, "12 of 16", "Cells off for the estimator's independent model.", C.accent3);
  stat(s, 6.8, 3.75, 2.7, "p ≤ 4·10⁻⁴", "Independence rejected in every setting.", C.text2, 26);
}

// ---------- 5. Scoreboard ----------
{
  const s = content("Results", "Nine rules fixed in advance: five passed, four failed",
    "Each rule was written down before its bases were reduced, and every outcome is reported. The failures were informative: R5 showed the per-level product is biased, R6 and R9 exposed the LLL effect, R7 lacked a degeneracy guard.");
  const R = [
    ["R5", false, "Fixed-error sphere model", "Off in 16 of 16 cells"],
    ["R6", false, "Exact law, LLL + BKZ", "Failed on LLL bases"],
    ["R7", false, "Exact law, BKZ", "Failed on a degenerate setting"],
    ["R8", true, "Exact law, BKZ, with guard", "0 of 16 off (independent: 12)"],
    ["R9", false, "Block-multiset law, LLL", "Narrow: 2 tail cells off"],
    ["R10", true, "Scale-up, BKZ-40, n = 120/150", "0 of 16 off (independent: 11)"],
    ["R11", true, "Scrambled LLL", "0 of 8 off (independent: 7)"],
    ["R12", true, "Pruned enumeration", "0 of 16 off (independent: 16)"],
    ["R13", true, "TU Darmstadt challenge data", "p = 0.095 (independent: 3·10⁻⁵)"],
  ];
  R.forEach(([name, pass, what, res], i) => {
    const x = 0.5 + (i % 3) * 3.07, y = 1.25 + Math.floor(i / 3) * 1.27;
    card(s, x, y, 2.9, 1.12, pass ? TEAL_TINT : CORAL_TINT);
    text(s, name, { x: x + 0.15, y: y + 0.12, w: 0.8, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
    text(s, pass ? "PASSED" : "FAILED", { x: x + 1.65, y: y + 0.14, w: 1.1, h: 0.3, fontSize: 11, bold: true, align: "right", color: pass ? C.accent5 : FAIL_TEXT });
    text(s, what, { x: x + 0.15, y: y + 0.5, w: 2.6, h: 0.27, fontSize: 12, bold: true });
    text(s, res, { x: x + 0.15, y: y + 0.78, w: 2.6, h: 0.27, fontSize: 12 });
  });
}

// ---------- 6. Outcomes ----------
{
  const s = content("Results", "Outcomes across attacks, sizes and real data",
    "Each row is a different setting. The exact law tracks the measurement; the independent model, which the estimator uses, misses it. With pruned enumeration about one instance in six is never solved however often you retry. On the n = 120 Babai row the two models are close because almost nothing is solved.");
  table(s, [
    ["Setting (rule)", "Quantity", "Measured", "Exact law", "Independent"],
    ["Babai, BKZ-20 n=95 η=3 (R8)", "Never solved in 64", "16.3%", "15.8%", "9.2%"],
    ["Babai, BKZ-40 n=120 η=2 (R10)", "Never solved in 64", "64.3%", "65.2%", "61.8%"],
    ["Enumeration, BKZ-10 n=85 η=3 (R12)", "Never solved in 64", "18.5%", "18.5%", "0.0%"],
    ["Enumeration, BKZ-40 n=150 η=2 (R10)", "Never solved in 32", "13.6%", "13.8%", "0.6%"],
    ["Scrambled LLL n=78 (R11)", "Cells off", "–", "0 of 8", "7 of 8"],
    ["TU Darmstadt challenge n=40/45 (R13)", "Goodness of fit, p", "–", "0.095", "3·10⁻⁵"],
    ["Babai, BKZ-20 n=100 η=3", "Attempts for 99%", "–", "4,097", "1,467"],
  ], { x: 0.5, y: 1.25, w: 9.0, colW: [3.3, 1.8, 1.2, 1.3, 1.4], rowH: 0.43, objectName: "outcomes_table" }, 4);
  text(s, "Exact law = our fixed-norm model, no fitted parameters. Independent = the lattice estimator's repetition model.", { x: 0.5, y: 4.8, w: 9.0, h: 0.3, fontSize: 11, italic: true, color: C.accent5 });
}

// ---------- 7. Theory and cost ----------
{
  const s = content("Results", "Why it happens, proven, and what it costs",
    "P1: at a fixed norm the per-level product overstates success. P2: averaged over Gaussian norms it is exactly right, which is why nobody noticed. P3: because every attempt shares the instance's norm, attempts are positively dependent, so amplify undercounts. The chart shows the measured cost: 1.25 to 2.8 times more attempts, growing as p falls.");
  const P = [
    ["P1", "Per instance, the estimator's formula is too high", "Checked: Π/F = 1.004–1.29"],
    ["P2", "Averaged over instances, it is exactly right", "Checked to 0.001 on 4 bases"],
    ["P3", "So amplify() always undercounts; restart after a failure", "Checked on all 6 cases"],
  ];
  P.forEach(([tag, head, chk], i) => {
    const y = 1.25 + i * 1.27;
    card(s, 0.5, y, 4.0, 1.12);
    badge(s, 0.68, y + 0.28, tag, C.accent1, 0.55);
    text(s, head, { x: 1.4, y: y + 0.13, w: 2.95, h: 0.55, fontSize: 13, bold: true, color: C.text2 });
    text(s, chk, { x: 1.4, y: y + 0.72, w: 2.95, h: 0.3, fontSize: 11, italic: true, color: C.accent5 });
  });
  s.addChart(pres.charts.BAR, [{ name: "Exact ÷ amplify", labels: ["33.6%", "19.6%", "9.5%", "3.9%", "3.7%", "0.31%"], values: [1.25, 1.28, 1.55, 1.62, 1.81, 2.79] }],
    chartOpts({ x: 4.75, y: 1.2, w: 4.85, h: 3.85, barDir: "col", chartColors: [H.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00\"×\"", valAxisMinVal: 0, valAxisMaxVal: 3.2, valAxisLabelFormatCode: "0.0", showLegend: false, showTitle: true, title: "Extra attempts for 99%: exact model ÷ amplify()", showCatAxisTitle: true, catAxisTitle: "Success per attempt", catAxisTitleFontSize: 10, catAxisTitleColor: H.accent4, catAxisTitleFontFace: "+mn-lt", objectName: "cost_chart" }));
}

// ---------- 8. Contributions ----------
pres.addSection({ title: "Contribution" });
{
  const s = content("Contribution", "Our contributions",
    "These are the contributions we claim, as far as the literature could be checked. The fixed-norm calculation itself goes back to Gama-Nguyen-Regev and Liu-Nguyen, so we do not claim it; what is new is showing that it is the missing ingredient in the repetition model, testing that in advance, and proving and pricing the consequences.");
  const items = [
    ["1", "First measurement", "Repeated decoding attempts on one LWE instance are dependent, in every setting tested."],
    ["2", "Explanation, tested in advance", "The instance's own error norm explains it (R8, R10, R12, R13); scrambled LLL needs the block-multiset law (R11)."],
    ["3", "Proofs P1–P3", "Per-instance bias of the estimator's formula, why it is right on average, and why amplify() undercounts."],
    ["4", "Cost and strategy", "1.25–2.8× more attempts for 99%; one instance in six never solved by enumeration; restart after one failure."],
    ["5", "Estimator patch", "A fixed_error repetition model for the lattice estimator; default output unchanged, doctests pass."],
  ];
  items.forEach(([num, head, body], i) => {
    const y = 1.15 + i * 0.68;
    badge(s, 0.5, y + 0.08, num, C.accent2, 0.45);
    text(s, head, { x: 1.15, y: y + 0.02, w: 2.6, h: 0.6, fontSize: 14, bold: true, color: C.text2, valign: "middle" });
    text(s, body, { x: 3.8, y: y + 0.02, w: 5.7, h: 0.6, fontSize: 13, valign: "middle" });
  });
  text(s, "Not claimed: the fixed-norm, random-direction calculation (Gama–Nguyen–Regev 2010; Liu–Nguyen 2013) or fixing the vector's length for uSVP (de Perthuis–Trenkić 2025).", { x: 0.5, y: 4.62, w: 9.0, h: 0.5, fontSize: 11, italic: true, color: C.accent5 });
}

// ---------- 9. Impact and limits ----------
{
  const s = content("Contribution", "Impact on estimates, and limits",
    "With our option, the Babai hybrid cost rises by up to 5 bits for Kyber512, but no best-attack estimate moves, because a different attack is cheaper there. Everything is at toy size. A stricter per-instance check found a small unexplained residual at BKZ-10. Next steps: read Wunderer's thesis, model the meet-in-the-middle step, and offer the patch upstream.");
  s.addChart(pres.charts.BAR, [{ name: "Bits added", labels: ["Kyber512", "HES ternary", "Concrete_TFHE586", "TFHE630", "TFHE1024", "SEAL20"], values: [4.99, 1.65, 1.18, 1.02, 0.65, 0.17] }],
    chartOpts({ x: 0.4, y: 1.2, w: 5.3, h: 3.85, barDir: "bar", chartColors: [H.accent5], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.00", valAxisMinVal: 0, valAxisMaxVal: 6, catAxisOrientation: "maxMin", showLegend: false, showTitle: true, title: "Babai hybrid (no MitM): bits added by our model", objectName: "impact_chart" }));
  text(s, "Limits", { x: 6.0, y: 1.25, w: 3.5, h: 0.35, fontSize: 15, bold: true, color: FAIL_TEXT });
  text(s, bullets(["Toy sizes; BKZ ≤ 40; Babai to n = 120.", "No best-attack estimate changes.", "Small residual at BKZ-10 (8–12%)."], 12), { x: 6.0, y: 1.65, w: 3.5, h: 1.4 });
  text(s, "Next", { x: 6.0, y: 3.1, w: 3.5, h: 0.35, fontSize: 15, bold: true, color: C.accent5 });
  text(s, bullets(["Read Wunderer's 2018 thesis.", "Model the MitM step's σ-dependence.", "Offer the patch upstream; write the paper."], 12), { x: 6.0, y: 3.5, w: 3.5, h: 1.5 });
}

// ---------- 10. References ----------
{
  const s = content("Contribution", "References",
    "References cited in the study. Liu-Nguyen 2013, Kirshanova-May-Wiemer 2016, de Perthuis-Trenkic 2025 and Luan et al. 2023 were read in full; Wunderer 2019 was searched in full text. Code, logs and the full write-up are on GitHub at github.com/sudu787/crypto_project.");
  const left = [
    "Lenstra, Lenstra, Lovász (1982). Factoring polynomials with rational coefficients. Math. Annalen 261.",
    "Babai (1986). On Lovász' lattice reduction and the nearest lattice point problem. Combinatorica 6.",
    "Schnorr, Euchner (1994). Lattice basis reduction: improved practical algorithms. Math. Programming 66.",
    "Regev (2005). On lattices, learning with errors, random linear codes, and cryptography. STOC 2005.",
    "Gama, Nguyen, Regev (2010). Lattice enumeration using extreme pruning. EUROCRYPT 2010.",
    "Chen, Nguyen (2011). BKZ 2.0: better lattice security estimates. ASIACRYPT 2011.",
    "Lindner, Peikert (2011). Better key sizes (and attacks) for LWE-based encryption. CT-RSA 2011.",
  ];
  const right = [
    "Liu, Nguyen (2013). Solving BDD by enumeration: an update. CT-RSA 2013, LNCS 7779.",
    "Albrecht, Player, Scott (2015). On the concrete hardness of LWE. J. Math. Cryptology 9.",
    "Buchmann et al. (2016). Creating cryptographic challenges using MPC: the LWE challenge. AsiaPKC 2016.",
    "Kirshanova, May, Wiemer (2016). Parallel implementation of BDD enumeration for LWE. ACNS 2016.",
    "Wunderer (2019). A detailed analysis of the hybrid lattice-reduction and MitM attack. J. Math. Cryptology 13.",
    "Luan, Shi, Gu, Zheng (2023). Application of discrete pruned enumeration in solving BDD. Symmetry 15.",
    "de Perthuis, Trenkić (2025). Refined modelling of the primal attack. ePrint 2025/2195, PQCrypto 2026.",
  ];
  const refs = (arr) => arr.map((r, i) => ({ text: r, options: { breakLine: i < arr.length - 1, paraSpaceAfter: 5, fontSize: 10.5 } }));
  text(s, refs(left), { x: 0.5, y: 1.2, w: 4.35, h: 3.85 });
  text(s, refs(right), { x: 5.15, y: 1.2, w: 4.35, h: 3.85 });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
