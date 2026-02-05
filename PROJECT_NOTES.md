# Smart Vending ATX Dashboard - Project Notes

## Current Status (Feb 4, 2026)

### ✅ Completed Features

#### 1. Core Dashboard
- Real-time analytics with revenue, profit, and margin tracking
- Multi-source data integration (HAHA POS, NAYAX, USAT/Cantaloupe)
- Dark theme with brand colors (#09fe94, #27a162, #267449)
- Logo integration in header

#### 2. Filtering & Controls
- Interactive date range filtering with calendar picker (react-datepicker)
- Date presets: Today, Yesterday, This Week, Last Week, This Month, Last Month, Custom
- Location-based filtering with sidebar (22 locations)
- Select all / Clear all location functionality

#### 3. Visualizations
**Revenue by Location** (Horizontal Bar Chart)
- 700px height for 22 locations
- Location labels inside bars (left-aligned)
- Green bars (#09fe94)

**Profit by Location + Margin %** (Combo Chart)
- 600px height
- Green bars (#09fe94) for profit (left Y-axis)
- White line (#ffffff) for margin % (right Y-axis, 0-100%)
- Rotated location labels at bottom

**Product Performance Scatter Chart**
- X-axis: Units Sold (Volume)
- Y-axis: Revenue ($)
- Dot size: Scaled by profit margin (60-400px)
- Color coding:
  - #09fe94: >70% margin (high performers)
  - #27a162: 50-70% margin (good performers)
  - #267449: <50% margin (needs attention)
- Reference lines for average volume & revenue (creates quadrants)
- Custom tooltip: Product Name, Revenue, Units Sold, Avg Price, Margin %
- Filters out products with <5 units sold

**Top 15 Products by Revenue** (Horizontal Bar Chart)
- Shows best-selling products by total sales
- Green bars (#09fe94)

**Top 15 Products by Margin %** (Horizontal Bar Chart)
- Shows most profitable products (5+ sales, cost data required)
- White bars (#ffffff)
- Y-axis starts at 60% with 10% increments (60, 70, 80, 90, 100)
- Only shows products with cost > 0

#### 4. Admin Interface (`/admin`)
- Web-based SKU mapping tool
- 3-column layout:
  - Left: Unmapped products (sorted by revenue impact)
  - Middle: Actions (suggestions, mapping controls)
  - Right: SKU map search (fuzzy search across 300+ products)
- Auto-suggests similar products using fuzzy matching
- Supports:
  - Mapping NAYAX products to existing SKUs
  - Updating costs for existing SKUs
  - Creating new products
- One-click "Save & Reprocess" button
- Automatically runs process_data.js after saving
- Excludes known issues: SKU0353 (Unknown), SKU0127 (Flock sample), SKU0318 (Steel Omni sample)

#### 5. Data Processing Scripts

**`scripts/process_data.js`** (Main processor)
- Consolidates 3 data sources: HAHA, NAYAX, USAT/Cantaloupe
- Loads SKU mappings with system-specific columns:
  - Haha_AI_Name (column F)
  - Nayax_Name (column G)
  - Cantaloupe_Name (column H)
- Outputs: `data/processed/master_dashboard_data.csv`
- Current results: 5,943 transactions, $23,513.98 revenue, $15,601.89 profit (66.3% margin)

**`scripts/check_unmapped_costs.js`**
- Identifies products with $0 cost but >$0 revenue
- Generates `unmapped_products_report.csv`
- Shows top 20 by revenue impact
- Provides instructions for updating costs

**`scripts/analyze_unmapped.js`**
- Categorizes unmapped products into:
  - Group A: Exists in SKU map, needs Nayax_Name column updated
  - Group B: New products, needs full SKU entry
  - Group C: Special cases requiring investigation

**`scripts/map_products_interactive.js`**
- CLI version (superseded by web admin interface)
- Interactive prompts for mapping products
- Kept for reference/backup

#### 6. Data Files Structure

```
data/
├── raw/
│   ├── Order details_2026-02-04 23_02_14_4463.csv (HAHA)
│   ├── Product Sales Details_2026-02-04 23_02_19_4464.csv (HAHA)
│   ├── DynamicTransactionsMonitorMega_2026-02-04T230141.csv (NAYAX)
│   ├── usat-transaction-log.csv (Cantaloupe)
│   └── Product SKU Map.csv (320 SKUs with cost mapping)
├── processed/
│   └── master_dashboard_data.csv (consolidated output)
└── archive/ (old files)
```

**CSV Structure:**
- Master file columns: date, location, Master_SKU, Master_Name, Product_Family, revenue, cost, quantity, profit, gross_margin_percent
- Location mapping: `location_mapping.csv` (22 locations)

#### 7. Technology Stack
- **Framework:** Next.js 16.1.6 with Turbopack
- **Charts:** Recharts (BarChart, ComposedChart, ScatterChart)
- **Date Picker:** react-datepicker with custom dark theme
- **Icons:** lucide-react
- **Styling:** Tailwind CSS with custom dark theme
- **Port:** localhost:3002

---

## 🚀 Deployment Instructions (Tonight)

### Vercel Deployment
1. Go to https://vercel.com and sign in with GitHub
2. Click "Add New Project" → Import `chrisono-collab/smart-vending-atx-dashboard`
3. Configure:
   - Framework: Next.js (auto-detected)
   - Build Command: `npm run build`
   - Output Directory: `.next`
4. Add Environment Variable:
   - `NODE_ENV=production`
5. Click "Deploy"
6. Your URL: `https://smart-vending-atx-dashboard.vercel.app`

**Note:** The processed data file (`master_dashboard_data.csv`) is now in the repo for initial deployment.

---

## 📋 TODO: Supabase Migration (Tomorrow)

### Goals
1. Move from CSV-based storage to PostgreSQL database
2. Enable real-time data updates without re-deploying
3. Add authentication for admin interface
4. Set up automated data sync from HAHA/NAYAX/USAT APIs (if available)

### Database Schema Design

**Tables to create:**

```sql
-- Locations
CREATE TABLE locations (
  id SERIAL PRIMARY KEY,
  code VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Products (SKU Master)
CREATE TABLE products (
  master_sku VARCHAR(50) PRIMARY KEY,
  master_name VARCHAR(255) NOT NULL,
  product_family VARCHAR(255),
  cost DECIMAL(10, 2) NOT NULL DEFAULT 0,
  status VARCHAR(50) DEFAULT 'Active',
  haha_ai_name VARCHAR(255),
  nayax_name VARCHAR(255),
  cantaloupe_name VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Transactions
CREATE TABLE transactions (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  location_code VARCHAR(50) REFERENCES locations(code),
  master_sku VARCHAR(50) REFERENCES products(master_sku),
  revenue DECIMAL(10, 2) NOT NULL,
  cost DECIMAL(10, 2) NOT NULL,
  quantity INTEGER NOT NULL,
  profit DECIMAL(10, 2) NOT NULL,
  gross_margin_percent DECIMAL(5, 2),
  source VARCHAR(50) NOT NULL, -- 'HAHA', 'NAYAX', 'USAT'
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_location ON transactions(location_code);
CREATE INDEX idx_transactions_sku ON transactions(master_sku);
CREATE INDEX idx_transactions_source ON transactions(source);
```

### Migration Steps

1. **Setup Supabase Project**
   - Create new project at https://supabase.com
   - Note connection string and API keys

2. **Create Database Schema**
   - Run SQL schema above in Supabase SQL Editor
   - Set up Row Level Security (RLS) policies

3. **Migrate Existing Data**
   - Write Node.js script to import CSV data to Supabase
   - Import locations → products → transactions (in order)

4. **Update Application Code**
   - Install: `npm install @supabase/supabase-js`
   - Create `lib/supabase.ts` client
   - Update `app/page.tsx` to fetch from Supabase instead of CSV
   - Update API routes to use Supabase
   - Update admin interface to save to database

5. **Add Authentication**
   - Enable Supabase Auth
   - Add login page at `/login`
   - Protect `/admin` route
   - Add user management

6. **Update Data Processing**
   - Modify `scripts/process_data.js` to insert into Supabase
   - Set up cron job or GitHub Action for automated sync
   - OR: Build API endpoints to accept data from HAHA/NAYAX/USAT

7. **Environment Variables for Vercel**
   ```
   NEXT_PUBLIC_SUPABASE_URL=your-project-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-key
   ```

---

## 🔐 Security Considerations

### Current (CSV-based)
- ✅ Sensitive data files excluded from Git (.gitignore)
- ✅ No authentication required (local development only)
- ⚠️ Admin interface publicly accessible
- ⚠️ Data hardcoded in deployment

### After Supabase Migration
- ✅ Row Level Security (RLS) policies
- ✅ User authentication for admin access
- ✅ API keys in environment variables
- ✅ Real-time data updates
- ✅ Audit trail (created_at, updated_at)

---

## 📊 Current Performance Metrics

### Data Summary (January 2026)
- **Total Transactions:** 5,943
- **Total Revenue:** $23,513.98
- **Total Profit:** $15,601.89
- **Overall Margin:** 66.3%

**By Source:**
- HAHA: $18,735.83 revenue (65.4% margin) - 4,029 transactions
- NAYAX: $4,166.65 revenue (67.1% margin) - 1,607 transactions
- USAT: $611.50 revenue (58.3% margin) - 307 transactions

**Unmapped Products:** 3 (excluded: Unknown, Flock sample, Steel Omni sample)

---

## 🛠️ Maintenance & Updates

### Regular Tasks
1. **Weekly:** Upload new CSV files to `data/raw/`
2. **Weekly:** Run `node scripts/process_data.js`
3. **Weekly:** Check `node scripts/check_unmapped_costs.js` for new products
4. **As Needed:** Use `/admin` interface to map new products
5. **Monthly:** Review product performance in scatter chart
6. **Monthly:** Analyze top/bottom performers

### After Supabase Migration
1. **Daily:** Automated data sync (via cron/GitHub Actions)
2. **Weekly:** Review unmapped products in `/admin`
3. **Monthly:** Database cleanup and optimization

---

## 📝 Known Issues & Limitations

### Current
1. ✅ **FIXED:** Date filtering was excluding some January dates
2. ✅ **FIXED:** Margin calculations were incorrect (NAYAX showed 100%)
3. ✅ **FIXED:** Duplicate SKUs in admin interface causing React key warnings
4. ⚠️ **TODO:** Manual CSV upload required for data updates
5. ⚠️ **TODO:** No authentication on admin interface

### After Supabase
- Will resolve #4 and #5 above

---

## 🔗 Resources

- **GitHub Repo:** https://github.com/chrisono-collab/smart-vending-atx-dashboard
- **Local Dev:** http://localhost:3002
- **Admin Interface:** http://localhost:3002/admin
- **Vercel Deployment:** https://smart-vending-atx-dashboard.vercel.app (pending)

---

## 💡 Future Enhancements

### Phase 1 (Completed)
- ✅ Multi-source data integration
- ✅ Interactive filtering
- ✅ Multiple chart types
- ✅ Web-based admin interface
- ✅ Product performance analysis

### Phase 2 (Tomorrow - Supabase)
- 🔲 Database migration
- 🔲 Authentication
- 🔲 Real-time data updates

### Phase 3 (Future)
- 🔲 API integrations (HAHA/NAYAX/USAT direct sync)
- 🔲 Predictive analytics (forecast sales/inventory)
- 🔲 Alerts & notifications (low stock, poor performers)
- 🔲 Mobile app
- 🔲 Export reports (PDF, Excel)
- 🔲 Multi-user support with roles
- 🔲 Inventory tracking integration
- 🔲 Automated reordering suggestions

---

## 📞 Support

**Built with:** Claude Sonnet 4.5 (Feb 4, 2026)
**Questions?** Review this document or conversation history

---

*Last Updated: February 4, 2026*
