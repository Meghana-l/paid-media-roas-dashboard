"""
Reads public/dashboard_data.json and injects it into the HTML template below,
writing the final public/index.html. Data is embedded inline (not fetched)
so the file opens standalone offline, as a Vercel static site, or in any
preview that can't fetch a sibling JSON file.
"""
import json

with open("public/dashboard_data.json") as f:
    DATA = json.load(f)

DATA_JSON = json.dumps(DATA)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Paid Media Performance &amp; Incrementality Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1" integrity="sha384-jb8JQMbMoBUzgWatfe6COACi2ljcDdZQ2OxczGA3bGNeWe+6DChMTBJemed7ZnvJ" crossorigin="anonymous"></script>
<style>
:root {
  --bg-primary:#f6f7fb; --bg-card:#ffffff; --bg-header:#161a30;
  --text-primary:#1d2027; --text-secondary:#6b7280; --text-on-dark:#f5f6ff;
  --c1:#4C72B0; --c2:#DD8452; --c3:#55A868; --c4:#C44E52;
  --positive:#1f9d55; --negative:#d64545; --neutral:#6c757d;
  --gap:16px; --radius:10px; --border:#e8e9ee;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:var(--bg-primary); color:var(--text-primary); line-height:1.5;
}
.wrap { max-width:1360px; margin:0 auto; padding:var(--gap); }
header {
  background:var(--bg-header); color:var(--text-on-dark);
  padding:22px 26px; border-radius:var(--radius); margin-bottom:var(--gap);
  display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;
}
header h1 { font-size:20px; font-weight:650; }
header p { font-size:13px; color:#aeb3d6; margin-top:4px; max-width:620px; }
.filters { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
.filters label { font-size:12px; color:#c4c8e8; }
.filters select {
  padding:7px 10px; border-radius:6px; border:1px solid rgba(255,255,255,.25);
  background:rgba(255,255,255,.08); color:var(--text-on-dark); font-size:13px;
}
.filters select option { background:var(--bg-header); color:#fff; }

.kpi-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:var(--gap); margin-bottom:var(--gap); }
.kpi-card { background:var(--bg-card); border-radius:var(--radius); padding:18px 20px; box-shadow:0 1px 3px rgba(0,0,0,.06); border:1px solid var(--border); }
.kpi-label { font-size:12px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.5px; margin-bottom:6px; }
.kpi-value { font-size:24px; font-weight:700; }
.kpi-sub { font-size:12px; color:var(--text-secondary); margin-top:4px; }
.kpi-sub.positive { color:var(--positive); font-weight:600; }
.kpi-sub.negative { color:var(--negative); font-weight:600; }

.row { display:grid; gap:var(--gap); margin-bottom:var(--gap); }
.row.two { grid-template-columns:1.3fr 1fr; }
.row.two-eq { grid-template-columns:1fr 1fr; }
@media (max-width:900px){ .row.two, .row.two-eq { grid-template-columns:1fr; } }

.card { background:var(--bg-card); border-radius:var(--radius); padding:18px 22px; box-shadow:0 1px 3px rgba(0,0,0,.06); border:1px solid var(--border); }
.card h3 { font-size:14px; font-weight:650; margin-bottom:4px; }
.card .hint { font-size:12px; color:var(--text-secondary); margin-bottom:12px; }
.card canvas { max-height:290px; }

.callout { border-left:4px solid var(--c1); background:#eef2fb; padding:14px 18px; border-radius:8px; font-size:13.5px; }
.callout.good { border-left-color:var(--positive); background:#eaf7ee; }
.callout b { font-weight:700; }
.flag-pill { display:inline-block; background:#fdece9; color:#b6372b; border-radius:999px; padding:2px 10px; font-size:12px; font-weight:600; margin-left:8px; }

table.data-table { width:100%; border-collapse:collapse; font-size:13px; }
table.data-table thead th {
  text-align:left; padding:9px 10px; border-bottom:2px solid var(--border);
  color:var(--text-secondary); font-weight:650; font-size:11.5px; text-transform:uppercase;
  letter-spacing:.4px; cursor:pointer; white-space:nowrap;
}
table.data-table thead th:hover { color:var(--text-primary); }
table.data-table tbody td { padding:9px 10px; border-bottom:1px solid #f1f1f5; }
table.data-table tbody tr:hover { background:#fafafe; }

footer { text-align:center; font-size:12px; color:var(--text-secondary); padding:18px 0 28px; }
footer a { color:var(--c1); text-decoration:none; }
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div>
      <h1>Paid Media Performance &amp; Incrementality Dashboard</h1>
      <p>Spend, ROAS and LTV:CAC by channel, plus a geo holdout test measuring
      how much revenue the campaign actually caused &mdash; not just correlated with.
      All figures are from a synthetic dataset built for methodology demonstration.</p>
    </div>
    <div class="filters">
      <label for="channelFilter">Channel</label>
      <select id="channelFilter" onchange="onFilterChange()">
        <option value="all">All channels</option>
      </select>
    </div>
  </header>

  <section class="kpi-row" id="kpiRow"></section>

  <section class="row two">
    <div class="card">
      <h3>Daily Spend vs. Revenue</h3>
      <div class="hint">Filter by channel above to isolate one line of business.</div>
      <canvas id="trendChart"></canvas>
    </div>
    <div class="card">
      <h3>ROAS by Channel</h3>
      <div class="hint">Revenue returned per dollar of spend.</div>
      <canvas id="roasChart"></canvas>
    </div>
  </section>

  <section class="row two-eq">
    <div class="card">
      <h3>6-Month LTV vs. CAC by Channel</h3>
      <div class="hint">LTV from a simple cohort repeat-purchase model; CAC proxied by channel CPA.</div>
      <canvas id="ltvChart"></canvas>
    </div>
    <div class="card">
      <h3>Incrementality: Exposed vs. Holdout Geos</h3>
      <div class="hint" id="incrementalityHint"></div>
      <canvas id="incChart"></canvas>
    </div>
  </section>

  <section class="row" style="grid-template-columns:1fr;">
    <div class="card" id="incrementalityCallout"></div>
  </section>

  <section class="row" style="grid-template-columns:1fr;">
    <div class="card" id="budgetCallout"></div>
  </section>

  <section class="card">
    <h3>Campaign Detail</h3>
    <div class="hint">Click a column header to sort. <span id="flagNote"></span></div>
    <div id="campaignTable"></div>
  </section>

  <footer>
    Synthetic data, generated for this project &middot; methodology in the repo README
  </footer>
</div>

<script>
const DATA = __DATA_JSON__;
const COLORS = ['#4C72B0','#DD8452','#55A868','#C44E52','#8172B3','#937860'];

function money(v){
  if (v===null||v===undefined) return '—';
  const sign = v<0 ? '-' : '';
  v = Math.abs(v);
  if (v>=1e6) return sign+'$'+(v/1e6).toFixed(2)+'M';
  if (v>=1e3) return sign+'$'+(v/1e3).toFixed(1)+'K';
  return sign+'$'+v.toFixed(0);
}
function num(v){
  if (v===null||v===undefined) return '—';
  if (v>=1e6) return (v/1e6).toFixed(1)+'M';
  if (v>=1e3) return (v/1e3).toFixed(1)+'K';
  return v.toLocaleString();
}

let charts = {};
let currentChannel = 'all';

function populateChannelFilter(){
  const sel = document.getElementById('channelFilter');
  DATA.channel_summary.map(r=>r.channel).sort().forEach(ch=>{
    const o = document.createElement('option');
    o.value = ch; o.textContent = ch;
    sel.appendChild(o);
  });
}

function renderKPIs(){
  const t = DATA.totals;
  const inc = DATA.incrementality;
  const cards = [
    {label:'Total Spend', value: money(t.total_spend)},
    {label:'Total Revenue', value: money(t.total_revenue)},
    {label:'Blended ROAS', value: t.blended_roas.toFixed(2)+'x'},
    {label:'Est. Incremental Revenue', value: money(inc.estimated_total_incremental_revenue),
     sub: inc.significant ? 'statistically significant lift' : 'not significant', subClass: inc.significant?'positive':'negative'},
    {label:'Data Integrity', value: num(t.clean_row_count)+' / '+num(t.raw_row_count)+' rows',
     sub: t.flagged_row_count+' flagged for review', subClass:'negative'},
  ];
  document.getElementById('kpiRow').innerHTML = cards.map(c => `
    <div class="kpi-card">
      <div class="kpi-label">${c.label}</div>
      <div class="kpi-value">${c.value}</div>
      ${c.sub ? `<div class="kpi-sub ${c.subClass||''}">${c.sub}</div>` : ''}
    </div>`).join('');
}

function filteredTrend(){
  if (currentChannel==='all'){
    const byDate = {};
    DATA.daily_trend.forEach(r=>{
      byDate[r.date] = byDate[r.date] || {date:r.date, spend:0, revenue:0};
      byDate[r.date].spend += r.spend;
      byDate[r.date].revenue += r.revenue;
    });
    return Object.values(byDate).sort((a,b)=>a.date.localeCompare(b.date));
  }
  return DATA.daily_trend.filter(r=>r.channel===currentChannel).sort((a,b)=>a.date.localeCompare(b.date));
}

function renderTrendChart(){
  const rows = filteredTrend();
  const ctx = document.getElementById('trendChart').getContext('2d');
  if (charts.trend) charts.trend.destroy();
  charts.trend = new Chart(ctx, {
    type:'line',
    data:{
      labels: rows.map(r=>r.date),
      datasets:[
        {label:'Spend', data:rows.map(r=>r.spend), borderColor:COLORS[3], backgroundColor:COLORS[3]+'22', tension:.25, pointRadius:0, borderWidth:2},
        {label:'Revenue', data:rows.map(r=>r.revenue), borderColor:COLORS[2], backgroundColor:COLORS[2]+'22', tension:.25, pointRadius:0, borderWidth:2},
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      interaction:{mode:'index', intersect:false},
      plugins:{ legend:{position:'top', labels:{usePointStyle:true}},
        tooltip:{callbacks:{label:(c)=> c.dataset.label+': '+money(c.parsed.y)}} },
      scales:{ x:{grid:{display:false}, ticks:{maxTicksLimit:8}},
        y:{beginAtZero:true, ticks:{callback:(v)=>money(v)}} }
    }
  });
}

function renderRoasChart(){
  const rows = [...DATA.channel_summary].sort((a,b)=>b.roas-a.roas);
  const ctx = document.getElementById('roasChart').getContext('2d');
  if (charts.roas) charts.roas.destroy();
  charts.roas = new Chart(ctx, {
    type:'bar',
    data:{ labels:rows.map(r=>r.channel),
      datasets:[{ data:rows.map(r=>r.roas), backgroundColor:COLORS, borderRadius:5 }] },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false}, tooltip:{callbacks:{label:(c)=>c.parsed.y.toFixed(2)+'x ROAS'}} },
      scales:{ y:{beginAtZero:true, ticks:{callback:(v)=>v.toFixed(1)+'x'}} } }
  });
}

function renderLtvChart(){
  const rows = [...DATA.ltv].sort((a,b)=>b.ltv_to_cac-a.ltv_to_cac);
  const ctx = document.getElementById('ltvChart').getContext('2d');
  if (charts.ltv) charts.ltv.destroy();
  charts.ltv = new Chart(ctx, {
    type:'bar',
    data:{ labels:rows.map(r=>r.channel),
      datasets:[
        {label:'6-mo LTV', data:rows.map(r=>r.ltv_6mo), backgroundColor:COLORS[2]+'CC', borderRadius:5},
        {label:'CAC', data:rows.map(r=>r.cac), backgroundColor:COLORS[3]+'CC', borderRadius:5},
      ] },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{position:'top'}, tooltip:{callbacks:{label:(c)=>c.dataset.label+': '+money(c.parsed.y)}} },
      scales:{ y:{beginAtZero:true, ticks:{callback:(v)=>money(v)}} } }
  });
}

function renderIncChart(){
  const ts = DATA.incrementality.timeseries;
  const ctx = document.getElementById('incChart').getContext('2d');
  if (charts.inc) charts.inc.destroy();
  charts.inc = new Chart(ctx, {
    type:'line',
    data:{ labels: ts.map(r=>r.date),
      datasets:[
        {label:'Exposed geos', data:ts.map(r=>r.exposed), borderColor:COLORS[0], pointRadius:0, borderWidth:2, tension:.2},
        {label:'Holdout geos', data:ts.map(r=>r.holdout), borderColor:COLORS[3], borderDash:[5,4], pointRadius:0, borderWidth:2, tension:.2},
      ] },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{position:'top'}, tooltip:{callbacks:{label:(c)=>c.dataset.label+': '+money(c.parsed.y)}} },
      scales:{ x:{ticks:{maxTicksLimit:8}}, y:{beginAtZero:true, ticks:{callback:(v)=>money(v)}} } }
  });
  document.getElementById('incrementalityHint').textContent =
    `Pre-period (first half): both groups track together. Campaign launches at the midpoint; exposed geos pull ahead after.`;
}

function renderIncrementalityCallout(){
  const inc = DATA.incrementality;
  const el = document.getElementById('incrementalityCallout');
  const trendNote = inc.parallel_trends_ok
    ? `Pre-period gap between groups was ${inc.pre_period_gap_pct}% &mdash; small enough that the comparison is fair.`
    : `Pre-period gap between groups was ${inc.pre_period_gap_pct}% &mdash; larger than ideal, so treat this estimate with caution.`;
  el.innerHTML = `
    <h3>What the holdout test says</h3>
    <div class="callout ${inc.significant ? 'good' : ''}" style="margin-top:10px;">
      Exposed geos averaged <b>${money(inc.post_exposed_avg_daily_revenue)}</b>/day vs
      <b>${money(inc.post_holdout_avg_daily_revenue)}</b>/day in holdout geos during the
      ${inc.test_window_days}-day test. Difference-in-differences estimate:
      <b>${money(inc.did_coefficient_per_dma_per_day)}</b> incremental revenue per geo per day
      (p ${inc.p_value_display}, ${inc.significant ? 'statistically significant' : 'not statistically significant'}).
      ${trendNote}
    </div>`;
}

function renderBudgetCallout(){
  const rows = [...DATA.ltv].sort((a,b)=>b.ltv_to_cac-a.ltv_to_cac);
  const best = rows[0], worst = rows[rows.length-1];
  const el = document.getElementById('budgetCallout');
  el.innerHTML = `
    <h3>Where the budget should probably move</h3>
    <div class="callout" style="margin-top:10px;">
      <b>${best.channel}</b> returns ${best.ltv_to_cac}x LTV:CAC, the strongest in the set.
      <b>${worst.channel}</b> returns only ${worst.ltv_to_cac}x. On an LTV:CAC basis alone,
      shifting incremental budget from ${worst.channel} toward ${best.channel} would raise
      blended payback efficiency &mdash; though the holdout test above matters more here than
      last-click ROAS, since last-click can overstate channels that just capture demand other
      channels already created.
    </div>`;
}

function renderCampaignTable(){
  const container = document.getElementById('campaignTable');
  let rows = [...DATA.campaign_summary];
  if (currentChannel!=='all') rows = rows.filter(r=>r.channel===currentChannel);
  let sortCol = 'spend', sortDir = 'desc';

  function draw(){
    const sorted = [...rows].sort((a,b)=>{
      const av=a[sortCol], bv=b[sortCol];
      const cmp = av<bv ? -1 : av>bv ? 1 : 0;
      return sortDir==='asc' ? cmp : -cmp;
    });
    const cols = [
      {f:'channel', l:'Channel'}, {f:'campaign', l:'Campaign'},
      {f:'spend', l:'Spend', fmt:money}, {f:'revenue', l:'Revenue', fmt:money},
      {f:'conversions', l:'Conversions', fmt:num}, {f:'roas', l:'ROAS', fmt:(v)=>v.toFixed(2)+'x'},
      {f:'cpa', l:'CPA', fmt:money},
    ];
    let html = '<table class="data-table"><thead><tr>';
    cols.forEach(c=>{
      const arrow = sortCol===c.f ? (sortDir==='asc'?' \u25b2':' \u25bc') : '';
      html += `<th onclick="sortCampaigns('${c.f}')">${c.l}${arrow}</th>`;
    });
    html += '</tr></thead><tbody>';
    sorted.forEach(r=>{
      html += '<tr>'+cols.map(c=>`<td>${c.fmt ? c.fmt(r[c.f]) : r[c.f]}</td>`).join('')+'</tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  }

  window.sortCampaigns = function(field){
    if (sortCol===field) sortDir = sortDir==='asc'?'desc':'asc';
    else { sortCol=field; sortDir='desc'; }
    draw();
  };
  draw();

  const t = DATA.totals;
  document.getElementById('flagNote').innerHTML =
    t.flagged_row_count>0 ? `<span class="flag-pill">${t.flagged_row_count} rows excluded &mdash; see data_quality_flags in the data file</span>` : '';
}

function onFilterChange(){
  currentChannel = document.getElementById('channelFilter').value;
  renderTrendChart();
  renderCampaignTable();
}

populateChannelFilter();
renderKPIs();
renderTrendChart();
renderRoasChart();
renderLtvChart();
renderIncChart();
renderIncrementalityCallout();
renderBudgetCallout();
renderCampaignTable();
</script>
</body>
</html>
"""

html = HTML_TEMPLATE.replace("__DATA_JSON__", DATA_JSON)
with open("public/index.html", "w") as f:
    f.write(html)

print(f"Wrote public/index.html ({len(html):,} bytes)")
