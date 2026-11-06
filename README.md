# Paid Media Performance & Incrementality Dashboard

A dashboard built on simulated ad spend data that looks at which channels
actually pay back, and whether a campaign's results are real or just
coincidence.

> ⚠️ All spend, click, and conversion figures here are made up, generated
> for this project. No real campaign or ad account data is used anywhere.

---

## The problem this solves

Most ad reporting stops at ROAS: revenue divided by spend. The problem is
ROAS can't tell you whether that revenue would have shown up anyway. A
retargeting ad can look amazing by "catching" people who were already about
to buy something. That's not the same as the ad actually causing the sale.

The only real way to check is to hold a comparable group of people back from
seeing the ad, and compare what happens to them against the group that did
see it. That's what the second half of this dashboard does: a held-out test
group, compared properly, to measure the actual lift an ad campaign caused.

## What's in the dashboard

**Channel performance** — spend, revenue, conversions, and ROAS for four
channels (Google Ads, Meta Ads, TikTok Ads, and Programmatic Display) over
180 days, filterable by channel.

**LTV vs. cost to acquire** — an estimate of how much a customer from each
channel is worth over 6 months, compared against how much it costs to
acquire them. Google Ads and Meta Ads pay back the fastest here; Programmatic
Display is the weakest, which is a real signal for where to shift budget.

**The holdout test** — 10 regions, 5 of them held back from seeing one
campaign. Before the campaign launched, both groups were tracking almost
identically, which is what makes the comparison fair. After launch, the
exposed group pulled ahead, and that gap is used to calculate the actual
revenue the campaign caused, along with how confident that estimate is.

**Data cleanup** — the raw data has the kind of mess real exports have:
duplicate rows, a few rows where spend was logged 100x too high, a few days
where a tracking tag broke and spend looked like zero even though sales kept
coming in, and a handful of rows with impossible numbers. All of this gets
caught and set aside rather than silently fixed, so nothing gets quietly
smoothed over.

## Tools and skills used

- **Python** to generate the data and run the analysis
- **SQL** to clean the raw data and build the summary tables
- Statistical testing to check whether the campaign's lift was real and not
  just noise
- A simple cohort model to estimate customer lifetime value per channel
- Automated tests (17 of them) checking that the cleaning rules and the
  calculations actually do what they're supposed to
- An interactive dashboard (HTML, JavaScript, Chart.js) with filtering and a
  sortable table, built to run entirely on its own with no server needed

## About the data

Every number in this project — spend, clicks, conversions, revenue, the
holdout test, all of it — is generated for this project. There is no real
client or ad account data anywhere here.

---

Built by Meghana Lakshminarayana Swamy · [meghana-l.github.io](https://meghana-l.github.io)
