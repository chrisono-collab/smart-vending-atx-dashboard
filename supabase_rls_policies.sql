-- Enable Row-Level Security and create policies for client-side uploads
-- Run this in Supabase SQL Editor

-- 1. Ensure RLS is enabled
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- 2. Allow public insert (needed for new transactions)
CREATE POLICY "Allow public insert"
ON public.transactions
FOR INSERT
TO anon
WITH CHECK (true);

-- 3. Allow public update (needed for upsert/deduplication)
CREATE POLICY "Allow public update"
ON public.transactions
FOR UPDATE
TO anon
USING (true)
WITH CHECK (true);

-- 4. Allow public select (needed for dashboard to read data)
CREATE POLICY "Allow public select"
ON public.transactions
FOR SELECT
TO anon
USING (true);

-- Verification query - should return the 4 policies above
SELECT * FROM pg_policies WHERE tablename = 'transactions';
