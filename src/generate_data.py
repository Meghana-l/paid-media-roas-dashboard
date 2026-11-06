"""
Generates synthetic paid media performance data.

Two datasets:
1. daily_performance: channel/campaign-level spend, clicks, conversions, revenue
   for 180 days across 4 channels, deliberately messy (dupes, nulls, a currency
   mismatch, a negative spend day) so the SQL cleaning layer has real work to do.
2. holdout_experiment: a geo holdout test for one flagship campaign -- half the
   regions see the campaign ("exposed"), half don't ("holdout") -- used to
   measure incremental revenue instead of just last-click attribution.

All data is fake. Generated, not scraped or pulled from any real ad account.
"""
import csv
import random
from datetime import date, timedelta

random.seed(42)

OUT_DIR = "data"
import os
os.makedirs(OUT_DIR, exist_ok=True)

CHANNELS = {
    "Google Ads":        {"base_cpc": 1.35, "base_cvr": 0.041, "base_aov": 68},
    "Meta Ads":          {"base_cpc": 0.92, "base_cvr": 0.028, "base_aov": 58},
    "TikTok Ads":        {"base_cpc": 0.61, "base_cvr": 0.019, "base_aov": 47},
    "Programmatic Display": {"base_cpc": 0.48, "base_cvr": 0.009, "base_aov": 52},
}

CAMPAIGNS = {
    "Google Ads": ["Brand Search", "Non-Brand Search", "Shopping"],
    "Meta Ads": ["Prospecting - Lookalike", "Retargeting - Cart Abandoners"],
    "TikTok Ads": ["Spark Ads - UGC"],
    "Programmatic Display": ["Display - Retargeting", "Display - Prospecting"],
}

START = date(2026, 4, 1)
DAYS = 180

rows = []
row_id = 1
for d in range(DAYS):
    the_date = START + timedelta(days=d)
    # mild weekly seasonality + a slow spend ramp over the period
    dow_factor = 1.15 if the_date.weekday() in (4, 5) else 1.0
    ramp = 1.0 + (d / DAYS) * 0.35

    for channel, params in CHANNELS.items():
        for campaign in CAMPAIGNS[channel]:
            budget_noise = random.uniform(0.8, 1.2)
            daily_spend = round(
                random.uniform(150, 600) * dow_factor * ramp * budget_noise, 2
            )
            cpc = max(0.1, random.gauss(params["base_cpc"], params["base_cpc"] * 0.15))
            clicks = max(0, int(daily_spend / cpc))
            impressions = int(clicks / random.uniform(0.015, 0.04))
            cvr = max(0.001, random.gauss(params["base_cvr"], params["base_cvr"] * 0.2))
            conversions = int(clicks * cvr)
            aov = max(10, random.gauss(params["base_aov"], params["base_aov"] * 0.12))
            revenue = round(conversions * aov, 2)

            row = {
                "row_id": row_id,
                "date": the_date.isoformat(),
                "channel": channel,
                "campaign": campaign,
                "impressions": impressions,
                "clicks": clicks,
                "spend": daily_spend,
                "conversions": conversions,
                "revenue": revenue,
            }
            rows.append(row)
            row_id += 1

# --- deliberately mess some of it up, same philosophy as the recruiting pipeline ---

# 1. Duplicate a handful of rows (double-counted exports happen in real life)
rows += random.sample(rows, 14)

# 2. A handful of rows with spend logged in cents instead of dollars (fat-finger export)
for r in random.sample(rows, 9):
    r = dict(r)
    r["spend"] = round(r["spend"] * 100, 2)
    r["row_id"] = row_id
    row_id += 1
    rows.append(r)

# 3. A short platform outage: Meta Ads reported $0 spend but real clicks/conversions
#    for 3 days (tracking pixel broke, not a real spend drop)
outage_dates = [START + timedelta(days=x) for x in (40, 41, 42)]
for r in rows:
    if r["channel"] == "Meta Ads" and date.fromisoformat(r["date"]) in outage_dates:
        r["spend"] = 0.0

# 4. A few rows with conversions exceeding clicks (bad postback data from one network)
for r in random.sample(rows, 6):
    r["conversions"] = r["clicks"] + random.randint(5, 20)

# 5. A few completely null campaign names (export truncation)
for r in random.sample(rows, 5):
    r["campaign"] = ""

random.shuffle(rows)

with open(f"{OUT_DIR}/daily_performance_raw.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"daily_performance_raw.csv: {len(rows)} rows")

# ---------------------------------------------------------------------------
# Holdout / incrementality experiment
#
# Flagship campaign: Meta Ads - "Prospecting - Lookalike"
# 10 comparable DMAs, randomly split 5 exposed / 5 holdout.
# Campaign launches on day 90 of the main window and runs 45 days.
# Pre-period (60 days before launch) shows both groups trending together.
# Post-period: exposed group should show a real lift if the channel works.
# ---------------------------------------------------------------------------
DMAS = [f"DMA-{i}" for i in range(1, 11)]
random.shuffle(DMAS)
EXPOSED = set(DMAS[:5])
HOLDOUT = set(DMAS[5:])

EXP_START = START + timedelta(days=60)   # pre-period begins
LAUNCH = START + timedelta(days=90)      # campaign turns on
EXP_END = LAUNCH + timedelta(days=45)    # test window ends

TRUE_LIFT = 0.22  # the "ground truth" incremental lift we're baking in, so the
                   # diff-in-diff analysis has something real to recover

exp_rows = []
for d in range((EXP_END - EXP_START).days):
    the_date = EXP_START + timedelta(days=d)
    is_post = the_date >= LAUNCH
    for dma in DMAS:
        base_daily_conversions = random.gauss(14, 2.5)
        base_daily_revenue = base_daily_conversions * random.gauss(55, 6)

        if is_post and dma in EXPOSED:
            base_daily_conversions *= (1 + TRUE_LIFT + random.gauss(0, 0.05))
            base_daily_revenue *= (1 + TRUE_LIFT + random.gauss(0, 0.05))

        exp_rows.append({
            "date": the_date.isoformat(),
            "dma": dma,
            "group": "exposed" if dma in EXPOSED else "holdout",
            "period": "post" if is_post else "pre",
            "conversions": max(0, round(base_daily_conversions, 1)),
            "revenue": max(0, round(base_daily_revenue, 2)),
        })

with open(f"{OUT_DIR}/holdout_experiment_raw.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(exp_rows[0].keys()))
    writer.writeheader()
    writer.writerows(exp_rows)

print(f"holdout_experiment_raw.csv: {len(exp_rows)} rows "
      f"({len(EXPOSED)} exposed DMAs, {len(HOLDOUT)} holdout DMAs)")
