-- Complete Supabase setup for client-side uploads
-- Run this entire script in Supabase SQL Editor

-- ============================================================
-- STEP 1: Drop existing policies (if any) to start clean
-- ============================================================
DROP POLICY IF EXISTS "Allow public insert" ON public.transactions;
DROP POLICY IF EXISTS "Allow public update" ON public.transactions;
DROP POLICY IF EXISTS "Allow public select" ON public.transactions;
DROP POLICY IF EXISTS "Allow public delete" ON public.transactions;

-- ============================================================
-- STEP 2: Ensure RLS is enabled
-- ============================================================
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- STEP 3: Create comprehensive RLS policies for anon role
-- ============================================================

-- Allow SELECT (crucial for upsert to check existing rows)
CREATE POLICY "Allow anon select"
ON public.transactions
FOR SELECT
TO anon, authenticated
USING (true);

-- Allow INSERT (for new transactions)
CREATE POLICY "Allow anon insert"
ON public.transactions
FOR INSERT
TO anon, authenticated
WITH CHECK (true);

-- Allow UPDATE (for upsert conflict resolution)
CREATE POLICY "Allow anon update"
ON public.transactions
FOR UPDATE
TO anon, authenticated
USING (true)
WITH CHECK (true);

-- Allow DELETE (optional, for future cleanup operations)
CREATE POLICY "Allow anon delete"
ON public.transactions
FOR DELETE
TO anon, authenticated
USING (true);

-- ============================================================
-- STEP 4: Ensure dedup_key has a UNIQUE constraint
-- ============================================================

-- First, check if constraint already exists
DO $$
BEGIN
    -- Drop existing constraint if it exists
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'transactions_dedup_key_unique'
    ) THEN
        ALTER TABLE transactions DROP CONSTRAINT transactions_dedup_key_unique;
    END IF;

    -- Create unique constraint on dedup_key
    ALTER TABLE transactions ADD CONSTRAINT transactions_dedup_key_unique UNIQUE (dedup_key);

    RAISE NOTICE 'Unique constraint on dedup_key created successfully';
EXCEPTION
    WHEN duplicate_table THEN
        RAISE NOTICE 'Constraint already exists';
    WHEN OTHERS THEN
        RAISE NOTICE 'Error creating constraint: %', SQLERRM;
END $$;

-- Create index on dedup_key for faster lookups (if not exists)
CREATE INDEX IF NOT EXISTS idx_transactions_dedup_key ON transactions(dedup_key);

-- ============================================================
-- STEP 5: Create index on date for faster filtering
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp);

-- ============================================================
-- STEP 6: Verification queries
-- ============================================================

-- Show all policies
SELECT schemaname, tablename, policyname, roles, cmd
FROM pg_policies
WHERE tablename = 'transactions';

-- Show all indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'transactions';

-- Show all constraints
SELECT conname, contype
FROM pg_constraint
WHERE conrelid = 'transactions'::regclass;

-- Show column names (for verification)
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'transactions'
ORDER BY ordinal_position;
