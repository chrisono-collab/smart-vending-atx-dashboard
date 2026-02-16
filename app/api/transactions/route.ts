import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

const supabase = createClient(supabaseUrl, supabaseKey);

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const startDate = searchParams.get('startDate');
    const endDate = searchParams.get('endDate');
    const locations = searchParams.get('locations')?.split(',').filter(Boolean);

    // Fetch ALL transactions using pagination
    let allData: any[] = [];
    let from = 0;
    const pageSize = 1000;
    let hasMore = true;

    while (hasMore) {
      let query = supabase
        .from('transactions')
        .select('*')
        .order('timestamp', { ascending: true })
        .order('id', { ascending: true })  // Tie-breaker prevents pagination ghosting
        .range(from, from + pageSize - 1);

      // Apply date filters if provided
      if (startDate) {
        query = query.gte('date', startDate);
      }
      if (endDate) {
        query = query.lte('date', endDate);
      }

      // Apply location filter if provided
      if (locations && locations.length > 0) {
        query = query.in('location', locations);
      }

      const { data, error } = await query;

      if (error) {
        console.error('Supabase error:', error);
        return NextResponse.json(
          { error: 'Failed to fetch transactions' },
          { status: 500 }
        );
      }

      if (data && data.length > 0) {
        allData = allData.concat(data);
        from += pageSize;
        hasMore = data.length === pageSize;
      } else {
        hasMore = false;
      }
    }

    const data = allData;

    // Transform data to match dashboard interface
    const transactions = data.map((row: any) => ({
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

    return NextResponse.json({
      transactions,
      count: transactions.length,
    });

  } catch (error: any) {
    console.error('API error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
