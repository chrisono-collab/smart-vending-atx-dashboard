-- Clear all transactions and start fresh
-- Run this in Supabase SQL Editor, then re-upload your file

DELETE FROM transactions;

-- Verify it's empty
SELECT COUNT(*) as remaining_transactions FROM transactions;
