-- Smart Vending ATX Dashboard - Supabase Schema
-- Run this in Supabase SQL Editor to create all tables

-- 1. Transactions table (main data)
CREATE TABLE IF NOT EXISTS transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMPTZ NOT NULL,
  date DATE NOT NULL,
  location TEXT NOT NULL,
  master_sku TEXT NOT NULL,
  master_name TEXT NOT NULL,
  product_family TEXT,
  type TEXT,
  revenue DECIMAL(10, 2) NOT NULL,
  cost DECIMAL(10, 2) NOT NULL,
  quantity INTEGER NOT NULL,
  profit DECIMAL(10, 2) NOT NULL,
  gross_margin_percent DECIMAL(5, 2),
  mapping_tier TEXT,
  dedup_key TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_location ON transactions(location);
CREATE INDEX IF NOT EXISTS idx_transactions_master_sku ON transactions(master_sku);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_dedup_key ON transactions(dedup_key);

-- 2. SKU Mappings table
CREATE TABLE IF NOT EXISTS sku_mappings (
  master_sku TEXT PRIMARY KEY,
  master_name TEXT NOT NULL,
  product_family TEXT,
  type TEXT,
  cost DECIMAL(10, 2),
  cantaloupe_name TEXT,
  haha_ai_name TEXT,
  nayax_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for SKU lookup
CREATE INDEX IF NOT EXISTS idx_sku_cantaloupe ON sku_mappings(cantaloupe_name) WHERE cantaloupe_name IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sku_haha_ai ON sku_mappings(haha_ai_name) WHERE haha_ai_name IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sku_nayax ON sku_mappings(nayax_name) WHERE nayax_name IS NOT NULL;

-- 3. Location Mappings table
CREATE TABLE IF NOT EXISTS location_mappings (
  raw_name TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Upload History table
CREATE TABLE IF NOT EXISTS upload_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  filename TEXT NOT NULL,
  upload_date TIMESTAMPTZ DEFAULT NOW(),
  total_transactions INTEGER,
  duplicates_removed INTEGER,
  mapping_coverage DECIMAL(5, 2),
  unmapped_revenue DECIMAL(10, 2),
  status TEXT NOT NULL,
  error_message TEXT,
  processed_at TIMESTAMPTZ
);

-- Index for upload history
CREATE INDEX IF NOT EXISTS idx_upload_history_date ON upload_history(upload_date DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sku_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE location_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_history ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all operations for service role, read-only for anon)
-- Transactions
CREATE POLICY "Allow service role all operations on transactions" ON transactions
  FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Allow anon read transactions" ON transactions
  FOR SELECT USING (true);

-- SKU Mappings
CREATE POLICY "Allow service role all operations on sku_mappings" ON sku_mappings
  FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Allow anon read sku_mappings" ON sku_mappings
  FOR SELECT USING (true);

-- Location Mappings
CREATE POLICY "Allow service role all operations on location_mappings" ON location_mappings
  FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Allow anon read location_mappings" ON location_mappings
  FOR SELECT USING (true);

-- Upload History
CREATE POLICY "Allow service role all operations on upload_history" ON upload_history
  FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Allow anon read upload_history" ON upload_history
  FOR SELECT USING (true);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_sku_mappings_updated_at
  BEFORE UPDATE ON sku_mappings
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_location_mappings_updated_at
  BEFORE UPDATE ON location_mappings
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
