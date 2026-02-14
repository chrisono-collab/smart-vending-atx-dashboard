import DashboardClient from "./DashboardClient";
import { createClient } from "@supabase/supabase-js";

export interface Transaction {
  date: string;
  location: string;
  Master_SKU: string;
  Master_Name: string;
  Product_Family: string;
  Type: string;
  revenue: number;
  cost: number;
  quantity: number;
  profit: number;
  gross_margin_percent: number;
  mapping_tier?: string;
}

async function fetchTransactions(): Promise<Transaction[]> {
  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const { data, error } = await supabase
      .from('transactions')
      .select('*')
      .order('date', { ascending: true });

    if (error) {
      console.error('Error fetching transactions:', error);
      return [];
    }

    // Transform Supabase data to match Transaction interface
    return data.map((row: any) => ({
      date: row.date,
      location: row.location,
      Master_SKU: row.master_sku,
      Master_Name: row.master_name,
      Product_Family: row.product_family || '',
      Type: row.type || 'Unknown',
      revenue: parseFloat(row.revenue),
      cost: parseFloat(row.cost),
      quantity: parseInt(row.quantity),
      profit: parseFloat(row.profit),
      gross_margin_percent: parseFloat(row.gross_margin_percent),
      mapping_tier: row.mapping_tier || undefined,
    }));
  } catch (error) {
    console.error('Error in fetchTransactions:', error);
    return [];
  }
}

export default async function Dashboard() {
  const transactions = await fetchTransactions();

  // Get unique locations
  const locations = Array.from(new Set(transactions.map(t => t.location))).sort();

  return <DashboardClient transactions={transactions} locations={locations} />;
}
