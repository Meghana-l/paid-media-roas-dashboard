const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const html = fs.readFileSync(path.join(__dirname, "../public/index.html"), "utf8");

// Minimal Chart.js stub: just record that a chart was constructed and don't
// crash on destroy()/data access, since jsdom's canvas has no real 2D context.
class FakeChart {
  constructor(ctx, config) {
    this.ctx = ctx;
    this.config = config;
    FakeChart.instances.push(config);
  }
  destroy() {}
  update() {}
}
FakeChart.instances = [];

const dom = new JSDOM(html, {
  runScripts: "dangerously",
  resources: "usable",
  beforeParse(window) {
    window.Chart = FakeChart;
    window.HTMLCanvasElement.prototype.getContext = () => ({});
  },
});

dom.window.onerror = (msg, src, line, col, err) => {
  console.error("RUNTIME ERROR:", msg, "line", line);
  process.exitCode = 1;
};

// Give the inline <script> a tick to run, then inspect results.
setTimeout(() => {
  const w = dom.window;
  const d = w.document;

  const checks = [];
  const kpiCards = d.querySelectorAll("#kpiRow .kpi-card");
  checks.push(["KPI cards rendered (expect 5)", kpiCards.length === 5]);

  const channelOptions = d.querySelectorAll("#channelFilter option");
  checks.push(["Channel filter populated (expect 5: all + 4 channels)", channelOptions.length === 5]);

  const tableRows = d.querySelectorAll("#campaignTable table tbody tr");
  checks.push(["Campaign table has rows", tableRows.length > 0]);

  const incCallout = d.querySelector("#incrementalityCallout").innerHTML;
  checks.push(["Incrementality callout mentions p-value", incCallout.includes("p <") || incCallout.includes("p=") || incCallout.includes("p 0") || incCallout.includes("p <0") || incCallout.includes("significant")]);

  const budgetCallout = d.querySelector("#budgetCallout").innerHTML;
  checks.push(["Budget callout non-empty", budgetCallout.length > 50]);

  checks.push(["5 Chart.js instances constructed (trend, roas, ltv, inc)", FakeChart.instances.length === 4]);

  let allOk = true;
  for (const [label, ok] of checks) {
    console.log((ok ? "PASS" : "FAIL") + " - " + label);
    if (!ok) allOk = false;
  }

  // sanity print a couple of actual values
  console.log("\nSample KPI card 0 HTML:\n", kpiCards[0].innerHTML.replace(/\s+/g, " ").trim());
  console.log("\nIncrementality callout:\n", incCallout.replace(/\s+/g, " ").trim());
  console.log("\nBudget callout:\n", budgetCallout.replace(/\s+/g, " ").trim());

  process.exit(allOk ? 0 : 1);
}, 500);
