-- Check for duplicate transactions

-- 1. Count total transactions
SELECT COUNT(*) as total_transactions FROM transactions;

-- 2. Count unique dedup_keys
SELECT COUNT(DISTINCT dedup_key) as unique_dedup_keys FROM transactions;

-- 3. Find duplicate dedup_keys
SELECT dedup_key, COUNT(*) as count
FROM transactions
GROUP BY dedup_key
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 20;

-- 4. February revenue breakdown
SELECT
    date,
    COUNT(*) as transaction_count,
    SUM(revenue) as daily_revenue
FROM transactions
WHERE date >= '2026-02-01' AND date < '2026-03-01'
GROUP BY date
ORDER BY date;

-- 5. Check for NULL dedup_keys
SELECT COUNT(*) as null_dedup_keys
FROM transactions
WHERE dedup_key IS NULL;

-- 6. Sample transactions from February
SELECT id, timestamp, date, location, master_name, revenue, dedup_key
FROM transactions
WHERE date >= '2026-02-01' AND date < '2026-03-01'
ORDER BY timestamp
LIMIT 10;
