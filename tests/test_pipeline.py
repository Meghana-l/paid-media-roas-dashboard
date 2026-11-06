"""
Tests the SQL cleaning rules and the incrementality math, run against a
fresh build of the warehouse so they always reflect what's actually shipped.
"""
import os
import sqlite3
import subprocess
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module", autouse=True)
def build_pipeline():
    subprocess.run([sys.executable, "src/generate_data.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "src/pipeline.py"], cwd=ROOT, check=True)


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(os.path.join(ROOT, "data/warehouse.db"))
    yield c
    c.close()


# ---------- raw data sanity ----------

def test_raw_file_exists():
    assert os.path.exists(os.path.join(ROOT, "data/daily_performance_raw.csv"))


def test_raw_has_injected_dupes(conn):
    df = pd.read_sql("SELECT row_id, COUNT(*) c FROM raw_daily_performance GROUP BY row_id HAVING c > 1", conn)
    assert len(df) > 0, "expected the generator's injected duplicate row_ids"


# ---------- cleaning rules ----------

def test_dedup_removes_duplicate_row_ids(conn):
    df = pd.read_sql("SELECT row_id, COUNT(*) c FROM clean_daily_performance GROUP BY row_id HAVING c > 1", conn)
    assert len(df) == 0, "clean table should have no duplicate row_ids"


def test_no_spend_outliers_remain(conn):
    df = pd.read_sql("SELECT spend FROM clean_daily_performance", conn)
    assert df["spend"].max() < 3000, "cents-vs-dollars fix should cap realistic daily spend"


def test_no_negative_spend(conn):
    df = pd.read_sql("SELECT spend FROM clean_daily_performance", conn)
    assert (df["spend"] >= 0).all()


def test_impossible_conversions_are_flagged_not_dropped(conn):
    flagged = pd.read_sql(
        "SELECT * FROM clean_daily_performance WHERE flag_conversions_exceed_clicks = 1", conn
    )
    assert len(flagged) > 0, "generator injects rows with conversions > clicks; they must be flagged"
    # and they must be excluded from the reporting tables
    in_summary = pd.read_sql("SELECT SUM(conversions) c FROM channel_summary", conn).iloc[0]["c"]
    in_raw = pd.read_sql(
        "SELECT SUM(conversions) c FROM clean_daily_performance WHERE flag_conversions_exceed_clicks = 0 AND flag_missing_campaign = 0",
        conn,
    ).iloc[0]["c"]
    assert in_summary == in_raw


def test_missing_campaign_flagged(conn):
    flagged = pd.read_sql(
        "SELECT * FROM clean_daily_performance WHERE flag_missing_campaign = 1", conn
    )
    assert len(flagged) > 0


def test_meta_outage_days_show_zero_spend_but_nonzero_conversions(conn):
    df = pd.read_sql(
        "SELECT date, spend, conversions FROM clean_daily_performance "
        "WHERE channel = 'Meta Ads' AND date IN ('2026-05-11','2026-05-12','2026-05-13')",
        conn,
    )
    assert (df["spend"] == 0).any()
    assert (df["conversions"] > 0).any(), "outage should break spend tracking, not real conversions"


# ---------- rollups ----------

def test_channel_summary_roas_is_positive(conn):
    df = pd.read_sql("SELECT roas FROM channel_summary", conn)
    assert (df["roas"] > 0).all()


def test_channel_spend_sums_match_clean_table(conn):
    channel_total = pd.read_sql("SELECT SUM(spend) s FROM channel_summary", conn).iloc[0]["s"]
    clean_total = pd.read_sql(
        "SELECT SUM(spend) s FROM clean_daily_performance "
        "WHERE flag_conversions_exceed_clicks = 0 AND flag_missing_campaign = 0",
        conn,
    ).iloc[0]["s"]
    assert round(channel_total, 2) == round(clean_total, 2)


# ---------- incrementality ----------

def test_dashboard_json_has_incrementality_block():
    import json
    data = json.load(open(os.path.join(ROOT, "public/dashboard_data.json")))
    inc = data["incrementality"]
    assert "did_coefficient_per_dma_per_day" in inc
    assert "p_value" in inc
    assert "parallel_trends_ok" in inc


def test_incrementality_recovers_a_positive_lift():
    import json
    data = json.load(open(os.path.join(ROOT, "public/dashboard_data.json")))
    inc = data["incrementality"]
    # TRUE_LIFT baked into the generator is positive and sizeable; the
    # recovered coefficient should be positive too (sign, not exact value)
    assert inc["did_coefficient_per_dma_per_day"] > 0


def test_parallel_trends_check_passes_on_this_seed():
    import json
    data = json.load(open(os.path.join(ROOT, "public/dashboard_data.json")))
    assert data["incrementality"]["pre_period_gap_pct"] < 10


# ---------- LTV ----------

def test_ltv_present_for_every_channel():
    import json
    data = json.load(open(os.path.join(ROOT, "public/dashboard_data.json")))
    channels_in_summary = {r["channel"] for r in data["channel_summary"]}
    channels_in_ltv = {r["channel"] for r in data["ltv"]}
    assert channels_in_summary == channels_in_ltv


def test_ltv_to_cac_is_positive_for_all_channels():
    import json
    data = json.load(open(os.path.join(ROOT, "public/dashboard_data.json")))
    for row in data["ltv"]:
        assert row["ltv_to_cac"] is None or row["ltv_to_cac"] > 0


# ---------- totals integrity ----------

def test_totals_blended_roas_matches_spend_and_revenue():
    import json
    data = json.load(open(os.path.join(ROOT, "public/dashboard_data.json")))
    t = data["totals"]
    expected = round(t["total_revenue"] / t["total_spend"], 2)
    assert t["blended_roas"] == expected


def test_flagged_row_count_matches_raw_minus_clean():
    import json
    data = json.load(open(os.path.join(ROOT, "public/dashboard_data.json")))
    t = data["totals"]
    assert t["flagged_row_count"] == t["raw_row_count"] - t["clean_row_count"]
