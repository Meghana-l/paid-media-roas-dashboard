-- Cleans raw_daily_performance into clean_daily_performance.
-- Each rule below fixes one specific problem that generate_data.py injected
-- on purpose, so the pipeline has something real to catch.

DROP TABLE IF EXISTS clean_daily_performance;

CREATE TABLE clean_daily_performance AS
WITH

-- 1. De-duplicate: same row_id should only ever appear once
deduped AS (
    SELECT DISTINCT * FROM raw_daily_performance
),

-- 2. Fix the cents-vs-dollars fat-finger rows: any spend more than 20x the
--    typical spend for that channel/campaign on that day is almost certainly
--    off by a factor of 100
spend_fixed AS (
    SELECT
        row_id, date, channel, campaign, impressions, clicks, conversions, revenue,
        CASE
            WHEN spend > 3000 THEN ROUND(spend / 100.0, 2)
            ELSE spend
        END AS spend
    FROM deduped
),

-- 3. Flag (not silently fix) rows where conversions > clicks -- that's
--    physically impossible and points to bad postback data upstream
flagged AS (
    SELECT *,
        CASE WHEN conversions > clicks THEN 1 ELSE 0 END AS flag_conversions_exceed_clicks,
        CASE WHEN campaign = '' OR campaign IS NULL THEN 1 ELSE 0 END AS flag_missing_campaign
    FROM spend_fixed
)

SELECT * FROM flagged;

-- Rows with flag_conversions_exceed_clicks = 1 are written out separately by
-- the pipeline for a human to check with the ad network, same as the bad
-- offers/missing emails in the recruiting pipeline -- a program shouldn't
-- guess at a fix for data that's actively impossible.
