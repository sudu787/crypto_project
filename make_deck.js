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

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625
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
pres.defineSlideMaster({
  title: "Closing dark",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.28, w: 9, h: 0.75, fontSize: 26, bold: true, color: C.background1, valign: "middle", margin: 0, align: "left" }, text: "" } },
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
function stat(s, x, y, w, big, label, color, size = 36) {
  text(s, big, { x, y, w, h: 0.75, fontSize: size, bold: true, color, fontFace: THEME.headFontFace, valign: "bottom" });
  text(s, label, { x, y: y + 0.82, w, h: 0.8, fontSize: 12, color: C.text1 });
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

// ---------- 1. Title ----------
pres.addSection({ title: "Introduction" });
{
  const s = pres.addSlide({ masterName: "Title dark", sectionTitle: "Introduction" });
  s.addText("Repeated lattice decoding attempts are not independent", { placeholder: "title" });
  s.addText("A pre-registered study on toy LWE: measurements, proofs and a lattice-estimator patch\nCrypto research project · November 2026", { placeholder: "body" });
  // lattice motif: dot grid with one target point and its nearest lattice point
  for (let r = 0; r < 6; r++) for (let c = 0; c < 5; c++) {
    const x = 6.75 + c * 0.6 + (r % 2) * 0.3, y = 0.75 + r * 0.7;
    s.addShape(pres.shapes.OVAL, { x, y, w: 0.13, h: 0.13, fill: { color: C.accent4 }, line: { type: "none" }, objectName: id("dot") });
  }
  s.addShape(pres.shapes.OVAL, { x: 7.95 + 0.3 - 0.02, y: 0.75 + 3 * 0.7 - 0.02, w: 0.17, h: 0.17, fill: { color: C.accent2 }, line: { type: "none" }, objectName: "nearest_point" });
  s.addShape(pres.shapes.OVAL, { x: 8.45, y: 2.55, w: 0.17, h: 0.17, fill: { color: C.accent1 }, line: { type: "none" }, objectName: "target_point" });
  s.addShape(pres.shapes.LINE, { x: 8.32, y: 2.64, w: 0.18, h: 0.27, line: { color: C.accent1, width: 1.5, dashType: "dash" }, flipH: true, objectName: "error_vector" });
  s.addNotes("The project asks whether the lattice estimator is right to treat repeated decoding attempts on one LWE instance as independent coin flips. Short answer: no, and we can say exactly why.");
}

// ---------- 2. Journey ----------
{
  const s = content("Introduction", "Three phases: two honest nulls, then a new result",
    "Phase 1 was the VA-ANP decoder, which turned out not to be novel and failed at scale. Phase 2 checked how well the estimator predicts decoding success; the gap came from under-reduced BKZ, so no contribution. Phase 3 is the retry-dependence result, which is new as far as the literature could be checked.");
  const cols = [
    ["1", C.accent4, "VA-ANP decoder", "New CVP decoder idea. Not novel, and it failed its tests at scale."],
    ["2", C.accent4, "Decoding prediction", "Estimator mispredicts Babai success; cause was under-reduced BKZ. CBD-exact error: null."],
    ["3", C.accent2, "Retry dependence", "Repeated attempts on one instance are dependent. Explained, proven and tested in advance."],
  ];
  cols.forEach(([num, col, head, body], i) => {
    const x = 0.5 + i * 3.1;
    card(s, x, 1.35, 2.8, 3.4, i === 2 ? "E3F2F0" : C.background2);
    badge(s, x + 0.3, 1.6, num, col, 0.5);
    text(s, head, { x: x + 0.3, y: 2.3, w: 2.25, h: 0.45, fontSize: 17, bold: true, color: C.text2 });
    text(s, body, { x: x + 0.3, y: 2.85, w: 2.25, h: 1.7, fontSize: 14 });
  });
}

// ---------- 3. Background ----------
pres.addSection({ title: "The question" });
{
  const s = content("The question", "The step we studied: decode, and retry on failure",
    "The primal attack ends with a decoding step. Babai succeeds exactly when the offset's projection on every Gram-Schmidt direction lies inside half that direction's length. If it fails, attackers re-randomise the basis and try again. The estimator turns a per-attempt probability p into a number of attempts with the amplify formula, which assumes independent trials.");
  text(s, bullets([
    "The primal attack on LWE ends by decoding a target t = As + e against a reduced lattice basis.",
    "Babai succeeds iff |⟨o, uᵢ⟩| < ‖b*ᵢ‖/2 at every level i, where o is the instance's offset (−s, e).",
    "On failure: re-randomise and re-reduce the basis, then try again.",
  ]), { x: 0.5, y: 1.35, w: 4.6, h: 3.4 });
  card(s, 5.5, 1.35, 4.0, 3.4, C.text2);
  text(s, "What the lattice estimator charges", { x: 5.8, y: 1.6, w: 3.4, h: 0.4, fontSize: 14, bold: true, color: C.accent1 });
  text(s, "attempts for 99%\n= log 0.01 / log(1 − p)", { x: 5.8, y: 2.15, w: 3.4, h: 0.8, fontSize: 18, bold: true, color: C.background1, fontFace: THEME.headFontFace });
  text(s, "Every attempt is treated as an independent coin flip with the same p. Liu–Nguyen 2013: success is \"heuristically multiplied by ℓ\". Wunderer 2019: Assumption 1, constant p.", { x: 5.8, y: 3.1, w: 3.4, h: 1.5, fontSize: 13, color: C.background2 });
}

// ---------- 4. The question ----------
{
  const s = content("The question", "But on one instance the error vector never changes",
    "Re-randomising the basis changes the direction of the error relative to the basis, but not its length. An instance with a short error is easy on every basis; one with a long error is hard on every basis. So successes cluster by instance, and the independent model overstates multi-attempt success.");
  card(s, 0.5, 1.35, 4.35, 3.4);
  badge(s, 0.75, 1.6, "?", C.accent3);
  text(s, "What the estimator assumes", { x: 1.3, y: 1.62, w: 3.3, h: 0.4, fontSize: 17, bold: true, color: C.text2 });
  text(s, bullets(["Every attempt has the same success probability p.", "Attempts are independent.", "So enough retries solve every instance."]), { x: 0.8, y: 2.3, w: 3.8, h: 2.2 });
  card(s, 5.15, 1.35, 4.35, 3.4, "E3F2F0");
  badge(s, 5.4, 1.6, "!", C.accent2);
  text(s, "What actually happens", { x: 5.95, y: 1.62, w: 3.3, h: 0.4, fontSize: 17, bold: true, color: C.text2 });
  text(s, bullets(["The instance's error e is fixed; only its direction changes between bases.", "Short ‖e‖: easy on every basis. Long ‖e‖: hard on every basis.", "Successes cluster by instance; some are never solved."]), { x: 5.45, y: 2.3, w: 3.8, h: 2.2 });
}

// ---------- 5. Phase 1 ----------
{
  const s = content("The question", "Phase 1: the formula was right, our inputs were not",
    "Before the retry question we checked the estimator's single-attempt prediction. It was badly off, but the cause was our BKZ bases, which were not run to convergence. On the real basis the formula is accurate. Two CBD ideas gave measured nulls.");
  const items = [
    ["50 pts", "Babai success at BKZ-20 n = 100: 54% predicted, 4% measured. Cause: under-reduced BKZ.", C.accent3],
    ["18 / 18", "Settings where the estimator's formula, on the real basis, falls inside the 99% interval.", C.accent2],
    ["≤ 0.7 pts", "Gaussian vs exact CBD error model, everywhere. A measured null.", C.accent4],
    ["28,800", "Lindner–Peikert decodings: the true point, when found, was always the shortest.", C.accent4],
  ];
  items.forEach(([big, lab, col], i) => {
    const x = 0.5 + i * 2.3;
    card(s, x, 1.45, 2.1, 2.9);
    stat(s, x + 0.2, 1.65, 1.75, big, lab, col, 26);
  });
}

// ---------- 6. R4 ----------
pres.addSection({ title: "Findings" });
{
  const s = content("Findings", "Independence is rejected in all 4 settings (R4)",
    "Count variance is the variance of the number of successes per instance. Under independence it is fixed by p. Measured, it is up to 3.8 times larger. A permutation test rejects independence at p at most 4e-4 everywhere.");
  s.addChart(pres.charts.BAR, [{ name: "Measured ÷ independent", labels: ["LLL n=80 η=2", "LLL n=80 η=3", "BKZ-20 n=100 η=2", "BKZ-20 n=100 η=3"], values: [3.80, 1.63, 1.51, 1.10] }],
    chartOpts({ x: 0.4, y: 1.2, w: 5.6, h: 3.8, barDir: "col", chartColors: [H.accent3], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0\"×\"", valAxisMinVal: 0, valAxisMaxVal: 4.5, valAxisLabelFormatCode: "0.0", showLegend: false, showTitle: true, title: "Variance of success counts per instance, relative to the independent model", objectName: "r4_chart" }));
  stat(s, 6.4, 1.3, 3.1, "p ≤ 4·10⁻⁴", "Permutation test against independence, every setting.", C.accent3);
  stat(s, 6.4, 3.0, 3.1, "256 vs 123", "Attempts to solve 95% of instances at LLL η=2: measured vs independent model.", C.text2);
}

// ---------- 7. Exact law ----------
{
  const s = content("Findings", "The exact fixed-norm law: no fitted parameters",
    "Fix the instance's own offset length, take its direction uniform on the sphere, and require every level to succeed jointly. We compute this with 200,000 random directions per basis on the GPU. It matches the measured per-attempt success; the estimator's per-level product at the true norm is 10 to 15 percent too high.");
  text(s, bullets([
    "Keep the instance's own ‖o‖; make its direction uniform on the sphere.",
    "Success = all levels inside at once (joint, not a product).",
    "200,000 directions per basis, on the GPU.",
    "Product of per-level probabilities at the true ‖o‖ is 10–15% too high.",
  ], 13), { x: 0.5, y: 1.35, w: 3.5, h: 3.6 });
  s.addChart(pres.charts.BAR, [
    { name: "Measured", labels: ["LLL n=80", "BKZ-20 n=100", "LLL n=76*", "BKZ-10 n=90*"], values: [2.39, 3.86, 1.86, 9.36] },
    { name: "Exact law", labels: ["LLL n=80", "BKZ-20 n=100", "LLL n=76*", "BKZ-10 n=90*"], values: [2.36, 3.85, 1.85, 9.19] },
    { name: "Per-level product", labels: ["LLL n=80", "BKZ-20 n=100", "LLL n=76*", "BKZ-10 n=90*"], values: [2.74, 4.34, 2.19, 10.01] },
  ], chartOpts({ x: 4.2, y: 1.2, w: 5.4, h: 3.8, barDir: "col", barGrouping: "clustered", chartColors: [H.dk2, H.accent2, H.accent3], showLegend: true, legendPos: "b", valAxisMinVal: 0, valAxisLabelFormatCode: "0\"%\"", showTitle: true, title: "Success per attempt (%), * = held out", objectName: "exact_chart" }));
}

// ---------- 8. Scoreboard ----------
{
  const s = content("Findings", "Nine rules fixed in advance: five passed, four failed",
    "Each rule was written into a script docstring before its bases were reduced. We report every one, including the failures. The failures were informative: R5 showed the product model is biased, R6 and R9 exposed the LLL effect, R7 lacked a degeneracy guard.");
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
    card(s, x, y, 2.9, 1.12, pass ? "E3F2F0" : "FBE9E4");
    text(s, name, { x: x + 0.15, y: y + 0.12, w: 0.8, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
    text(s, pass ? "PASSED" : "FAILED", { x: x + 1.65, y: y + 0.14, w: 1.1, h: 0.3, fontSize: 11, bold: true, align: "right", color: pass ? C.accent5 : "B5462B" });
    text(s, what, { x: x + 0.15, y: y + 0.5, w: 2.6, h: 0.27, fontSize: 12, bold: true });
    text(s, res, { x: x + 0.15, y: y + 0.78, w: 2.6, h: 0.27, fontSize: 12 });
  });
}

// ---------- 9. R8 ----------
{
  const s = content("Findings", "Fresh instances: the exact law predicts the spread (R8)",
    "R8 used 2,048 fresh BKZ bases. The exact law predicted the variance of success counts within 3 to 6 percent; the independent model was off by a factor of 2 to 3. Cells are the solved-within-k shares at several k and the never-solved share.");
  s.addChart(pres.charts.BAR, [
    { name: "Measured", labels: ["BKZ-20 n=95 η=2", "BKZ-20 n=95 η=3", "BKZ-10 n=85 η=2", "BKZ-10 n=85 η=3"], values: [23.19, 3.94, 39.79, 12.39] },
    { name: "Exact law", labels: ["BKZ-20 n=95 η=2", "BKZ-20 n=95 η=3", "BKZ-10 n=85 η=2", "BKZ-10 n=85 η=3"], values: [22.56, 3.69, 38.14, 11.79] },
    { name: "Independent", labels: ["BKZ-20 n=95 η=2", "BKZ-20 n=95 η=3", "BKZ-10 n=85 η=2", "BKZ-10 n=85 η=3"], values: [10.06, 2.25, 14.41, 5.55] },
  ], chartOpts({ x: 0.4, y: 1.2, w: 6.0, h: 3.8, barDir: "col", barGrouping: "clustered", chartColors: [H.dk2, H.accent2, H.accent3], showLegend: true, legendPos: "b", valAxisMinVal: 0, showTitle: true, title: "Variance of success counts per instance (64 attempts)", objectName: "r8_chart" }));
  stat(s, 6.8, 1.3, 2.7, "0 of 16", "Cells off for the exact law.", C.accent2);
  stat(s, 6.8, 3.0, 2.7, "12 of 16", "Cells off for the estimator's independent model.", C.accent3);
}

// ---------- 10. Theory ----------
pres.addSection({ title: "Theory and cost" });
{
  const s = content("Theory and cost", "Three proven results explain the pattern",
    "P1: at a fixed norm the levels are negatively dependent, so the product overstates success for any one instance. P2: averaged over Gaussian norms, the product is exactly right, which is why the estimator looks fine on average. P3: success is a decreasing function of the norm shared by every attempt, so attempts are positively dependent and amplify undercounts.");
  const P = [
    ["P1", "Per instance, the product is too high", "Exact law F(r) ≤ per-level product Π(r) at every norm r.", "Check: 0 violations; Π/F = 1.004–1.29"],
    ["P2", "Averaged over instances, it is right", "Gaussian error: ∏ erf = E over ‖e‖ of F. Errors cancel on average.", "Check: agree to 0.001 on 4 bases"],
    ["P3", "So amplify() undercounts", "P(all K fail) ≥ ∏(1 − p̄). Hazard never rises; restart after a failure is optimal.", "Check: holds on all 6 cases"],
  ];
  P.forEach(([tag, head, body, chk], i) => {
    const x = 0.5 + i * 3.1;
    card(s, x, 1.35, 2.8, 3.4);
    badge(s, x + 0.25, 1.6, tag, C.accent1, 0.55);
    text(s, head, { x: x + 0.25, y: 2.3, w: 2.35, h: 0.65, fontSize: 15, bold: true, color: C.text2 });
    text(s, body, { x: x + 0.25, y: 3.0, w: 2.35, h: 1.0, fontSize: 13 });
    text(s, chk, { x: x + 0.25, y: 4.1, w: 2.35, h: 0.5, fontSize: 11, italic: true, color: C.accent5 });
  });
}

// ---------- 11. Cost ----------
{
  const s = content("Theory and cost", "Dependence costs 1.25–2.8× more attempts",
    "For 99 percent of instances to be solved, the exact model needs more attempts than amplify, and the gap grows as the per-attempt probability falls. If fresh instances are available, abandoning an instance after one failure is optimal.");
  s.addChart(pres.charts.BAR, [{ name: "Exact ÷ amplify", labels: ["p = 33.6%", "p = 19.6%", "p = 9.5%", "p = 3.9%", "p = 3.7%", "p = 0.31%"], values: [1.25, 1.28, 1.55, 1.62, 1.81, 2.79] }],
    chartOpts({ x: 0.4, y: 1.2, w: 5.8, h: 3.8, barDir: "col", chartColors: [H.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00\"×\"", valAxisMinVal: 0, valAxisMaxVal: 3.2, valAxisLabelFormatCode: "0.0", showLegend: false, showTitle: true, title: "Attempts for 99% of instances: exact model ÷ amplify(0.99, p)", objectName: "cost_chart" }));
  stat(s, 6.6, 1.3, 2.9, "4,097", "Attempts for 99% at p = 0.31% (BKZ-20 n=100 η=3). amplify() says 1,467.", C.text2);
  stat(s, 6.6, 3.0, 2.9, "Restart", "Give-up rule: after one failure, take a fresh instance. Retrying the same one costs up to 1.44× more.", C.accent5);
}

// ---------- 12. Enumeration + scale ----------
pres.addSection({ title: "Generality" });
{
  const s = content("Generality", "Enumeration: one instance in six is never solved",
    "With linear-pruning enumeration the fixed-norm law does not depend on the basis at all, so re-randomising can only help through the direction. About one sixth of instances are never solved however many attempts are made. The independent model predicts none. The same holds at n = 150 with BKZ-40 (R10).");
  const rows = [
    ["Setting", "Rule", "Measured", "Fixed-norm law", "Independent"],
    ["BKZ-20 n=95 η=2", "R12", "14.0%", "14.1%", "0.0%"],
    ["BKZ-20 n=95 η=3", "R12", "16.4%", "16.3%", "0.0%"],
    ["BKZ-10 n=85 η=2", "R12", "16.7%", "16.6%", "0.0%"],
    ["BKZ-10 n=85 η=3", "R12", "18.5%", "18.5%", "0.0%"],
    ["BKZ-40 n=150 η=1 (32 tries)", "R10", "10.1%", "9.5%", "0.6%"],
    ["BKZ-40 n=150 η=2 (32 tries)", "R10", "13.6%", "13.8%", "0.6%"],
  ];
  const tr = rows.map((r, i) => r.map((c, j) => ({ text: c, options: i === 0
    ? { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 12 }
    : { color: j === 4 ? "B5462B" : C.text1, bold: j === 2, fill: { color: i % 2 ? C.background1 : C.background2 }, fontSize: 12 } })));
  s.addTable(tr, { x: 0.5, y: 1.3, w: 9.0, colW: [3.0, 0.9, 1.6, 1.9, 1.6], rowH: 0.42, border: { type: "none" }, align: "left", valign: "middle", margin: [0, 0.08, 0, 0.08], objectName: "enum_table" });
  text(s, "Share of instances never solved in 64 attempts (32 for R10). Babai at n ≥ 150 succeeds ≈ 0% here, so Babai was scaled only to n = 120 (R10 passed there too).", { x: 0.5, y: 4.4, w: 9.0, h: 0.6, fontSize: 12, italic: true, color: C.accent5 });
}

// ---------- 13. LLL + real data ----------
{
  const s = content("Generality", "Also holds for scrambled LLL and real challenge data",
    "LLL's last Gram-Schmidt directions put 69 percent of their mass on the secret block, so success depends on the secret and error norms separately. With scrambled re-randomisation the block-multiset law explains it (R11). On TU Darmstadt LWE challenge files, the exact law fits and independence does not (R13); the evidence comes mostly from n = 40.");
  card(s, 0.5, 1.35, 4.35, 3.55);
  text(s, "LLL bases (R11)", { x: 0.75, y: 1.5, w: 3.9, h: 0.4, fontSize: 17, bold: true, color: C.text2 });
  text(s, bullets(["LLL puts 69% of its last Gram–Schmidt mass on the secret block (BKZ-20: 56%).", "So ‖s‖ and ‖e‖ matter separately.", "Scrambled re-randomisation + block-multiset law: 0 of 8 cells off (independent: 7)."], 13), { x: 0.75, y: 2.0, w: 3.9, h: 2.8 });
  card(s, 5.15, 1.35, 4.35, 3.55);
  text(s, "TU Darmstadt challenge (R13)", { x: 5.4, y: 1.5, w: 3.9, h: 0.4, fontSize: 17, bold: true, color: C.text2 });
  s.addChart(pres.charts.BAR, [
    { name: "Measured", labels: ["‖e‖² = 0.88× mean", "‖e‖² = 1.27× mean"], values: [22, 6] },
    { name: "Independent model", labels: ["‖e‖² = 0.88× mean", "‖e‖² = 1.27× mean"], values: [13, 13] },
  ], chartOpts({ x: 5.3, y: 1.9, w: 4.1, h: 2.2, barDir: "col", barGrouping: "clustered", chartColors: [H.dk2, H.accent3], showValue: true, dataLabelPosition: "outEnd", valAxisMinVal: 0, valAxisMaxVal: 26, showLegend: true, legendPos: "b", legendFontSize: 10, catAxisLabelFontSize: 10, showTitle: true, title: "Times solved in 64 attempts, n = 40", objectName: "r13_chart" }));
  text(s, "24 instances: X² = 33.4 (p = 0.095) exact vs 62.5 (p = 3·10⁻⁵) independent.", { x: 5.4, y: 4.2, w: 3.9, h: 0.6, fontSize: 12 });
}

// ---------- 14. Estimator ----------
pres.addSection({ title: "Impact and novelty" });
{
  const s = content("Impact and novelty", "Estimator patch: up to +5 bits, no headline change",
    "We added repetition_model equal to fixed_error to the lattice estimator. The default is unchanged and all doctests pass. For the Babai hybrid without meet-in-the-middle the cost rises by up to 5 bits for Kyber512. No best-attack estimate moves, because where the shift is largest uSVP or BDD is already cheaper. The patch is local and has not been submitted.");
  s.addChart(pres.charts.BAR, [{ name: "Bits added", labels: ["Kyber512", "HES ternary", "Concrete_TFHE586", "TFHE630", "TFHE1024", "SEAL20"], values: [4.99, 1.65, 1.18, 1.02, 0.65, 0.17] }],
    chartOpts({ x: 0.4, y: 1.2, w: 5.6, h: 3.8, barDir: "bar", chartColors: [H.accent5], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.00", valAxisMinVal: 0, valAxisMaxVal: 6, catAxisOrientation: "maxMin", showLegend: false, showTitle: true, title: "Babai hybrid (no MitM): bits added by the fixed-error model", objectName: "impact_chart" }));
  text(s, bullets([
    "New fixed_error repetition model; default output unchanged; 15 doctests pass.",
    "With MitM: Kyber512 +1.73 bits, others ≤ 0.15.",
    "No best-attack estimate moves: uSVP/BDD is cheaper where the shift is largest.",
    "Local patch, not yet submitted upstream.",
  ], 13), { x: 6.3, y: 1.35, w: 3.2, h: 3.6 });
}

// ---------- 15. Novelty ----------
{
  const s = content("Impact and novelty", "What is new, and what is not",
    "We read Liu-Nguyen 2013 first-hand. They assume success multiplies by the number of bases and never condition on the instance's own error norm. The fixed-norm computation itself is from Gama-Nguyen-Regev and Liu-Nguyen, so we do not claim it. What is new is measuring the dependence, showing what explains it, proving the consequences, and quantifying the cost.");
  card(s, 0.5, 1.35, 4.35, 3.55, "E3F2F0");
  text(s, "New, as far as checked", { x: 0.75, y: 1.5, w: 3.9, h: 0.4, fontSize: 17, bold: true, color: C.accent5 });
  text(s, bullets(["Measured dependence of repeated decoding attempts on one instance.", "Conditioning on the instance's own ‖e‖ explains almost all of it (R8, R10, R12, R13).", "Proofs P1–P3; cost and give-up rule.", "A tested estimator option."], 13), { x: 0.75, y: 2.0, w: 3.9, h: 2.8 });
  card(s, 5.15, 1.35, 4.35, 3.55);
  text(s, "Not new", { x: 5.4, y: 1.5, w: 3.9, h: 0.4, fontSize: 17, bold: true, color: "B5462B" });
  text(s, bullets(["The fixed-norm, uniform-direction computation (Gama–Nguyen–Regev; Liu–Nguyen 2013).", "Fixing the vector's length for uSVP (de Perthuis–Trenkić 2025).", "Read: Liu–Nguyen 2013, KMW 2016, 2025/2195, Luan et al. 2023, Wunderer 2019. Not yet read: Wunderer's 2018 thesis."], 13), { x: 5.4, y: 2.0, w: 3.9, h: 2.8 });
}

// ---------- 16. Close ----------
{
  const s = pres.addSlide({ masterName: "Closing dark", sectionTitle: "Impact and novelty" });
  s.addText("Limits and next steps", { placeholder: "title" });
  s.addNotes("Everything here is at toy size. The next steps are to finish the literature check, model the meet-in-the-middle step properly, and offer the estimator patch upstream. Code, logs and the full write-up are on GitHub.");
  text(s, "Limits", { x: 0.5, y: 1.3, w: 4.3, h: 0.4, fontSize: 17, bold: true, color: C.accent1 });
  text(s, bullets(["Toy parameters; BKZ block size ≤ 40.", "Babai tested only to n = 120 (≈ 0% success beyond).", "MitM success kept independent of σ in the patch.", "No published best-attack estimate changes."], 14), { x: 0.5, y: 1.8, w: 4.3, h: 2.6, color: C.background1 });
  text(s, "Next", { x: 5.2, y: 1.3, w: 4.3, h: 0.4, fontSize: 17, bold: true, color: C.accent1 });
  text(s, bullets(["Read Wunderer's 2018 thesis (needs the correct PDF).", "Check the GPU hybrid paper, ePrint 2025/1990.", "Model the MitM step's dependence on σ.", "Offer the patch upstream; write the paper."], 14), { x: 5.2, y: 1.8, w: 4.3, h: 2.6, color: C.background1 });
  text(s, "Code, logs and write-up: github.com/sudu787/crypto_project", { x: 0.5, y: 4.75, w: 8.0, h: 0.35, fontSize: 12, color: C.background2, hyperlink: { url: "https://github.com/sudu787/crypto_project" } });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
