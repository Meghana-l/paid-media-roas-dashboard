# Paid Media Performance & Incrementality Dashboard

**Live: [paid-media-roas-dashboard.vercel.app](https://paid-media-roas-dashboard.vercel.app/)**

A paid media analytics dashboard on simulated ad spend data, built to answer
the two questions every media budget eventually comes down to: which
channels are actually worth the spend, and did this specific campaign cause
incremental revenue or just take credit for sales that would've happened
anyway.

> All figures are generated synthetically for this project. No real
> campaign, client, or ad account data is used anywhere.

---

## The question ROAS can't answer

ROAS (revenue ÷ spend) is the default metric in most media reporting, and
it's a correlation, not a causal measure. A retargeting campaign can post an
8x ROAS by reaching people who were already about to convert — that's
credit, not incrementality. Budget decisions made on last-click ROAS alone
can systematically overfund channels that simply capture demand other
channels already created.

This project separates the two: standard channel-level reporting (spend,
ROAS, CPA, LTV:CAC), plus a geo holdout test that isolates the revenue a
campaign actually caused.

## What's in the dashboard

**Channel performance** — 180 days of spend, revenue, conversions, and ROAS
across four channels (Google Ads, Meta Ads, TikTok Ads, Programmatic
Display), filterable by channel. Blended ROAS across all channels: **1.64x**.

**LTV : CAC by channel** — a 6-month LTV estimate from a cohort
repeat-purchase model, measured against CAC (channel CPA). Google Ads leads
at **5.95x** LTV:CAC; Programmatic Display trails at **1.47x** — a
reallocation signal that last-click ROAS alone wouldn't surface as clearly.

**Incrementality test** — a geo holdout: 10 markets, 5 exposed to a Meta Ads
campaign and 5 held out. Pre-period trends between groups differed by only
**2.5%**, which is tight enough to trust the comparison. Post-launch, a
difference-in-differences model estimated **$862.63 in incremental revenue
per market per day** (p < 0.0001) — roughly **$194K in incremental revenue**
attributable to the campaign over the 45-day test window, not just
correlated with it.

**Data quality** — the raw feed carries the kind of issues real ad exports
produce: duplicate rows, a spend field logged in cents on some rows, a
3-day tracking outage where spend read $0 while conversions kept posting,
and rows with conversions exceeding clicks (a postback error, not a metric).
25 of 1,463 rows were flagged and excluded from reporting rather than
silently corrected — a dashboard that reconciles perfectly usually means
something got smoothed over.

## Tools and methodology

- **Python** — data generation and the analysis pipeline
- **SQL** — cleaning rules and reporting rollups, run against a local
  warehouse
- **Difference-in-differences regression** (with robust standard errors) —
  the incrementality estimate and its significance test
- **Cohort-based LTV modeling** — channel-level lifetime value vs. CAC
- **17 automated tests** — covering the cleaning logic, the rollups, and the
  incrementality math, so the numbers on the dashboard are the numbers the
  tests verify
- **Chart.js**, embedded data, zero backend — the dashboard is a single
  static page

---

Built by Meghana Lakshminarayana Swamy · [meghana-l.github.io](https://meghana-l.github.io)
