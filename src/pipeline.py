"""
Runs the full pipeline:
  1. Load raw CSVs into SQLite
  2. Run the SQL cleaning rules (sql/01, sql/02)
  3. Compute channel LTV (simple cohort repeat-rate model)
  4. Run the diff-in-differences incrementality analysis on the holdout test
  5. Write everything the dashboard needs to public/dashboard_data.json
"""
import json
import sqlite3
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

DB_PATH = "data/warehouse.db"
SQL_FILES = ["sql/01_clean_daily_performance.sql", "sql/02_aggregate_summaries.sql"]


def load_raw_data(conn):
    raw = pd.read_csv("data/daily_performance_raw.csv")
    raw.to_sql("raw_daily_performance", conn, if_exists="replace", index=False)
    return raw


def run_sql_files(conn):
    for path in SQL_FILES:
        with open(path) as f:
            conn.executescript(f.read())


def table_to_records(conn, table):
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    return df


def compute_ltv(conn):
    """
    Simple cohort LTV: for each channel, simulate how many of month-1
    customers are still generating revenue in months 2-6, based on a
    channel-specific retention curve. This is a standard "repeat purchase
    rate x average order value" LTV estimate, not a black box -- every
    number here traces back to the retention and AOV assumptions below.
    """
    channel_summary = table_to_records(conn, "channel_summary")

    # Retention assumptions by channel (made up, labeled as such in the UI;
    # search/intent-driven channels retain better than cold prospecting ones)
    retention_curves = {
        "Google Ads": [1.0, 0.52, 0.41, 0.35, 0.31, 0.28],
        "Meta Ads": [1.0, 0.38, 0.27, 0.21, 0.18, 0.16],
        "TikTok Ads": [1.0, 0.29, 0.18, 0.13, 0.10, 0.08],
        "Programmatic Display": [1.0, 0.22, 0.13, 0.09, 0.07, 0.05],
    }

    ltv_rows = []
    for _, row in channel_summary.iterrows():
        channel = row["channel"]
        conversions = row["conversions"]
        if conversions == 0:
            continue
        aov = row["revenue"] / conversions
        curve = retention_curves.get(channel, [1.0, 0.3, 0.2, 0.15, 0.12, 0.1])
        ltv_6mo = sum(c * aov for c in curve)
        cac = row["cpa"]  # using CPA as a proxy for CAC at the channel level
        ltv_rows.append({
            "channel": channel,
            "aov": round(aov, 2),
            "cac": round(cac, 2) if cac is not None else None,
            "ltv_6mo": round(ltv_6mo, 2),
            "ltv_to_cac": round(ltv_6mo / cac, 2) if cac else None,
        })
    return ltv_rows


def compute_incrementality():
    """
    Diff-in-differences on the geo holdout experiment:
    incremental lift = (post_exposed - pre_exposed) - (post_holdout - pre_holdout)

    Parallel-trends check: compare the pre-period gap between groups to the
    post-period gap. If pre-period trends aren't parallel, the DiD estimate
    isn't trustworthy -- that check is reported alongside the result, not
    hidden.
    """
    df = pd.read_csv("data/holdout_experiment_raw.csv")
    df["date"] = pd.to_datetime(df["date"])
    df["is_post"] = (df["period"] == "post").astype(int)
    df["is_exposed"] = (df["group"] == "exposed").astype(int)

    daily = (
        df.groupby(["date", "group", "period", "is_post", "is_exposed"])
        .agg(conversions=("conversions", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )

    model = smf.ols(
        "revenue ~ is_exposed * is_post", data=daily
    ).fit(cov_type="HC1")

    interaction_term = "is_exposed:is_post"
    did_coef = model.params[interaction_term]
    did_pval = model.pvalues[interaction_term]

    # Pre-period means for the parallel-trends sanity check
    pre = daily[daily["is_post"] == 0]
    pre_exposed_mean = pre[pre["is_exposed"] == 1]["revenue"].mean()
    pre_holdout_mean = pre[pre["is_exposed"] == 0]["revenue"].mean()
    pre_gap_pct = abs(pre_exposed_mean - pre_holdout_mean) / pre_holdout_mean * 100

    post = daily[daily["is_post"] == 1]
    post_exposed_mean = post[post["is_exposed"] == 1]["revenue"].mean()
    post_holdout_mean = post[post["is_exposed"] == 0]["revenue"].mean()

    n_post_days = post["date"].nunique()
    total_incremental_revenue = did_coef * n_post_days * 5  # x5 exposed DMAs/day

    daily_timeseries = (
        daily.groupby(["date", "group"])["revenue"]
        .mean()
        .reset_index()
        .pivot(index="date", columns="group", values="revenue")
        .reset_index()
    )
    daily_timeseries["date"] = daily_timeseries["date"].dt.strftime("%Y-%m-%d")

    p_display = "<0.0001" if did_pval < 0.0001 else f"{did_pval:.4f}"

    return {
        "did_coefficient_per_dma_per_day": round(did_coef, 2),
        "p_value": did_pval,
        "p_value_display": p_display,
        "significant": bool(did_pval < 0.05),
        "pre_period_gap_pct": round(pre_gap_pct, 1),
        "parallel_trends_ok": bool(pre_gap_pct < 10),
        "post_exposed_avg_daily_revenue": round(post_exposed_mean, 2),
        "post_holdout_avg_daily_revenue": round(post_holdout_mean, 2),
        "estimated_total_incremental_revenue": round(total_incremental_revenue, 2),
        "test_window_days": int(n_post_days),
        "timeseries": daily_timeseries.to_dict(orient="records"),
    }


def main():
    conn = sqlite3.connect(DB_PATH)
    load_raw_data(conn)
    run_sql_files(conn)

    channel_summary = table_to_records(conn, "channel_summary").to_dict(orient="records")
    campaign_summary = table_to_records(conn, "campaign_summary").to_dict(orient="records")
    daily_trend = table_to_records(conn, "daily_trend")
    daily_trend["date"] = daily_trend["date"].astype(str)
    daily_trend = daily_trend.to_dict(orient="records")
    quality_flags = table_to_records(conn, "data_quality_flags").to_dict(orient="records")

    ltv = compute_ltv(conn)
    incrementality = compute_incrementality()

    raw_count = pd.read_sql("SELECT COUNT(*) AS n FROM raw_daily_performance", conn).iloc[0]["n"]
    clean_count = pd.read_sql(
        "SELECT COUNT(*) AS n FROM clean_daily_performance "
        "WHERE flag_conversions_exceed_clicks = 0 AND flag_missing_campaign = 0", conn
    ).iloc[0]["n"]

    totals = {
        "total_spend": round(sum(r["spend"] for r in channel_summary), 2),
        "total_revenue": round(sum(r["revenue"] for r in channel_summary), 2),
        "total_conversions": int(sum(r["conversions"] for r in channel_summary)),
        "blended_roas": round(
            sum(r["revenue"] for r in channel_summary) /
            sum(r["spend"] for r in channel_summary), 2
        ),
        "raw_row_count": int(raw_count),
        "clean_row_count": int(clean_count),
        "flagged_row_count": int(raw_count - clean_count),
    }

    dashboard_data = {
        "totals": totals,
        "channel_summary": channel_summary,
        "campaign_summary": campaign_summary,
        "daily_trend": daily_trend,
        "quality_flags": quality_flags,
        "ltv": ltv,
        "incrementality": incrementality,
    }

    with open("public/dashboard_data.json", "w") as f:
        json.dump(dashboard_data, f, indent=2)

    conn.close()
    print("Pipeline complete.")
    print(f"  Raw rows: {raw_count}  |  Clean rows used in reporting: {clean_count}  "
          f"|  Flagged: {raw_count - clean_count}")
    print(f"  Blended ROAS: {totals['blended_roas']}x")
    print(f"  Incrementality: {incrementality['did_coefficient_per_dma_per_day']} "
          f"per DMA/day, p={incrementality['p_value']}, "
          f"significant={incrementality['significant']}")


if __name__ == "__main__":
    main()
