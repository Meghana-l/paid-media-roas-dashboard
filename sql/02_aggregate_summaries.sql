-- Builds the reporting layer on top of clean_daily_performance.
-- Rows missing a campaign name or flagged as impossible are excluded from
-- the reporting tables (they're flagged for review, not deleted).

DROP TABLE IF EXISTS channel_summary;
CREATE TABLE channel_summary AS
SELECT
    channel,
    COUNT(*) AS day_count,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(spend) AS spend,
    SUM(conversions) AS conversions,
    SUM(revenue) AS revenue,
    ROUND(SUM(revenue) * 1.0 / NULLIF(SUM(spend), 0), 2) AS roas,
    ROUND(SUM(spend) * 1.0 / NULLIF(SUM(conversions), 0), 2) AS cpa,
    ROUND(SUM(spend) * 1.0 / NULLIF(SUM(clicks), 0), 2) AS cpc,
    ROUND(SUM(clicks) * 100.0 / NULLIF(SUM(impressions), 0), 2) AS ctr_pct
FROM clean_daily_performance
WHERE flag_conversions_exceed_clicks = 0 AND flag_missing_campaign = 0
GROUP BY channel;

DROP TABLE IF EXISTS campaign_summary;
CREATE TABLE campaign_summary AS
SELECT
    channel,
    campaign,
    SUM(spend) AS spend,
    SUM(revenue) AS revenue,
    SUM(conversions) AS conversions,
    ROUND(SUM(revenue) * 1.0 / NULLIF(SUM(spend), 0), 2) AS roas,
    ROUND(SUM(spend) * 1.0 / NULLIF(SUM(conversions), 0), 2) AS cpa
FROM clean_daily_performance
WHERE flag_conversions_exceed_clicks = 0 AND flag_missing_campaign = 0
GROUP BY channel, campaign;

DROP TABLE IF EXISTS daily_trend;
CREATE TABLE daily_trend AS
SELECT
    date,
    channel,
    SUM(spend) AS spend,
    SUM(revenue) AS revenue,
    SUM(conversions) AS conversions
FROM clean_daily_performance
WHERE flag_conversions_exceed_clicks = 0 AND flag_missing_campaign = 0
GROUP BY date, channel
ORDER BY date;

DROP TABLE IF EXISTS data_quality_flags;
CREATE TABLE data_quality_flags AS
SELECT row_id, date, channel, campaign, clicks, conversions,
       flag_conversions_exceed_clicks, flag_missing_campaign
FROM clean_daily_performance
WHERE flag_conversions_exceed_clicks = 1 OR flag_missing_campaign = 1;
