-- ================================================
-- Stock Market Analytics Platform
-- SQL Query Library
-- ================================================


-- ------------------------------------------------
-- 1. Overall average closing price per stock
-- ------------------------------------------------
SELECT 
    c.company_name,
    sp.ticker,
    ROUND(AVG(sp.close)::numeric, 2) AS avg_close_price
FROM stock_prices sp
JOIN companies c ON sp.ticker = c.ticker
GROUP BY c.company_name, sp.ticker
ORDER BY avg_close_price DESC;


-- ------------------------------------------------
-- 2. Best performing stock (yearly return)
-- ------------------------------------------------
SELECT 
    ticker,
    ROUND(first_close::numeric, 2) AS start_price,
    ROUND(last_close::numeric, 2) AS end_price,
    ROUND(((last_close - first_close) / first_close * 100)::numeric, 2) AS yearly_return_pct
FROM (
    SELECT 
        ticker,
        FIRST_VALUE(close) OVER (PARTITION BY ticker ORDER BY date ASC) AS first_close,
        FIRST_VALUE(close) OVER (PARTITION BY ticker ORDER BY date DESC) AS last_close
    FROM stock_prices
) sub
GROUP BY ticker, first_close, last_close
ORDER BY yearly_return_pct DESC;


-- ------------------------------------------------
-- 3. Average return by sector
-- ------------------------------------------------
SELECT 
    s.sector_name,
    ROUND(AVG((sp_last.close - sp_first.close) / sp_first.close * 100)::numeric, 2) AS avg_return_pct
FROM companies c
JOIN sectors s ON c.sector_id = s.sector_id
JOIN (
    SELECT DISTINCT ON (ticker) ticker, close
    FROM stock_prices
    ORDER BY ticker, date ASC
) sp_first ON c.ticker = sp_first.ticker
JOIN (
    SELECT DISTINCT ON (ticker) ticker, close
    FROM stock_prices
    ORDER BY ticker, date DESC
) sp_last ON c.ticker = sp_last.ticker
GROUP BY s.sector_name
ORDER BY avg_return_pct DESC;


-- ------------------------------------------------
-- 4. Most volatile stock (std dev of daily returns)
-- ------------------------------------------------
SELECT 
    ticker,
    ROUND(STDDEV(daily_return)::numeric * 100, 4) AS volatility_pct
FROM (
    SELECT 
        ticker,
        date,
        (close - LAG(close) OVER (PARTITION BY ticker ORDER BY date)) 
        / LAG(close) OVER (PARTITION BY ticker ORDER BY date) AS daily_return
    FROM stock_prices
) sub
WHERE daily_return IS NOT NULL
GROUP BY ticker
ORDER BY volatility_pct DESC;


-- ------------------------------------------------
-- 5. Stocks nearest to their 52 week high
-- ------------------------------------------------
SELECT 
    sp.ticker,
    c.company_name,
    ROUND(MAX(sp.high)::numeric, 2) AS week_52_high,
    ROUND(latest.close::numeric, 2) AS current_price,
    ROUND(((latest.close - MAX(sp.high)) / MAX(sp.high) * 100)::numeric, 2) AS pct_from_high
FROM stock_prices sp
JOIN companies c ON sp.ticker = c.ticker
JOIN (
    SELECT DISTINCT ON (ticker) ticker, close
    FROM stock_prices
    ORDER BY ticker, date DESC
) latest ON sp.ticker = latest.ticker
GROUP BY sp.ticker, c.company_name, latest.close
ORDER BY pct_from_high DESC;


-- ------------------------------------------------
-- 6. Highest average volume by sector
-- ------------------------------------------------
SELECT 
    s.sector_name,
    ROUND(AVG(sp.volume)) AS avg_daily_volume
FROM stock_prices sp
JOIN companies c ON sp.ticker = c.ticker
JOIN sectors s ON c.sector_id = s.sector_id
GROUP BY s.sector_name
ORDER BY avg_daily_volume DESC;


-- ------------------------------------------------
-- 7. Top 5 highest volume trading days per stock
-- ------------------------------------------------
SELECT 
    ticker,
    date,
    volume
FROM (
    SELECT 
        ticker,
        date,
        volume,
        RANK() OVER (PARTITION BY ticker ORDER BY volume DESC) AS volume_rank
    FROM stock_prices
) ranked
WHERE volume_rank <= 5
ORDER BY ticker, volume_rank;