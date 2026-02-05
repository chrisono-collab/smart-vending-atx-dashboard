const fs = require('fs');
const path = require('path');

// File paths
const RAW_DIR = path.join(__dirname, '../data/raw');
const PROCESSED_DIR = path.join(__dirname, '../data/processed');
const HAHA_ORDER_FILE = 'Order details_2026-02-04 23_02_14_4463.csv';
const HAHA_PRODUCT_FILE = 'Product Sales Details_2026-02-04 23_02_19_4464.csv';
const NAYAX_FILE = 'DynamicTransactionsMonitorMega_2026-02-04T230141.csv';
const USAT_FILE = 'usat-transaction-log.csv';
const LOCATION_MAP_FILE = path.join(__dirname, '../location_mapping.csv');
const SKU_MAP_FILE = path.join(__dirname, '../data/raw/Product SKU Map.csv');

// Helper: Parse CSV
function parseCSV(filePath, skipRows = 1) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.trim().split('\n');
  const headers = lines[skipRows].split(',').map(h => h.trim());
  const data = [];

  for (let i = skipRows + 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i]);
    if (values.length === headers.length) {
      const row = {};
      headers.forEach((header, index) => {
        row[header] = values[index]?.trim() || '';
      });
      data.push(row);
    }
  }
  return data;
}

// Helper: Parse CSV line (handles commas in quotes)
function parseCSVLine(line) {
  const values = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      values.push(current.replace(/^"|"$/g, '')); // Remove surrounding quotes
      current = '';
    } else {
      current += char;
    }
  }
  values.push(current.replace(/^"|"$/g, ''));
  return values;
}

// Helper: Parse date from MM/DD/YYYY HH:MM:SS to YYYY-MM-DD
function parseDate(dateStr) {
  if (!dateStr) return null;
  const parts = dateStr.split(' ')[0].split('/');
  if (parts.length !== 3) return null;
  const [month, day, year] = parts;
  return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
}

// Helper: Check if date is in January 2026
function isJanuary2026(dateStr) {
  return dateStr && dateStr.startsWith('2026-01');
}

// Load location mapping
function loadLocationMapping() {
  const map = {};
  const content = fs.readFileSync(LOCATION_MAP_FILE, 'utf-8');
  const lines = content.trim().split('\n').slice(1); // Skip header

  lines.forEach(line => {
    const [raw, display] = line.split(',').map(s => s.trim().replace(/"/g, ''));
    if (raw && display) {
      map[raw] = display;
    }
  });

  return map;
}

// Load SKU mapping (creates lookups for HAHA, NAYAX, and Cantaloupe)
function loadSKUMapping() {
  const hahaMap = {};
  const nayaxMap = {};
  const cantaloupeMap = {};

  try {
    const content = fs.readFileSync(SKU_MAP_FILE, 'utf-8');
    const lines = content.trim().split('\n').slice(1); // Skip header

    lines.forEach(line => {
      const values = parseCSVLine(line);
      const masterSKU = values[0]?.trim();
      const masterName = values[1]?.trim();
      const productFamily = values[2]?.trim();
      const costStr = values[3]?.trim() || '$0';
      const cost = parseFloat(costStr.replace(/[$,]/g, '')) || 0;
      const hahaName = values[5]?.trim();
      const nayaxName = values[6]?.trim();
      const cantaloupeName = values[7]?.trim();

      const skuInfo = {
        Master_SKU: masterSKU,
        Master_Name: masterName,
        Product_Family: productFamily,
        cost: cost
      };

      // Map HAHA product names
      if (hahaName) {
        hahaMap[hahaName] = skuInfo;
      }

      // Map NAYAX product names
      if (nayaxName) {
        nayaxMap[nayaxName] = skuInfo;
      }

      // Map Cantaloupe product names
      if (cantaloupeName) {
        cantaloupeMap[cantaloupeName] = skuInfo;
      }
    });
  } catch (error) {
    console.warn('SKU mapping file not found, using product names as SKUs');
  }

  return { hahaMap, nayaxMap, cantaloupeMap };
}

// Process HAHA Product Sales Details
function processHAHAProducts(locationMap, hahaMap) {
  console.log('\n=== Processing HAHA Product Sales Details ===');
  const filePath = path.join(RAW_DIR, HAHA_PRODUCT_FILE);
  const products = parseCSV(filePath);

  const transactions = [];
  let januaryCount = 0;
  let januaryRevenue = 0;
  let januaryCost = 0;

  products.forEach(row => {
    const date = parseDate(row['Creation time']);
    if (!isJanuary2026(date)) return;

    const deviceNumber = row['Device number'];
    const location = locationMap[deviceNumber] || deviceNumber;
    const productName = row['Product'];
    const revenue = parseFloat(row['Amount Receivable']?.replace(/[$,]/g, '')) || 0;
    const quantity = parseFloat(row['Sales volume']?.replace(/[$,]/g, '')) || 1;

    // Get SKU mapping cost (prioritize this over CSV cost)
    const skuInfo = hahaMap[productName];
    const cost = skuInfo?.cost || 0; // Use SKU map cost, default to 0 if not found
    const profit = revenue - cost;
    const marginPercent = revenue > 0 ? (profit / revenue * 100) : 0;

    transactions.push({
      date,
      location,
      Master_SKU: skuInfo?.Master_SKU || 'UNMAPPED',
      Master_Name: skuInfo?.Master_Name || productName,
      Product_Family: skuInfo?.Product_Family || productName,
      revenue,
      cost,
      quantity,
      profit,
      gross_margin_percent: marginPercent
    });

    januaryCount++;
    januaryRevenue += revenue;
    januaryCost += cost;
  });

  console.log(`  Processed ${januaryCount} HAHA transactions`);
  console.log(`  Total HAHA revenue: $${januaryRevenue.toFixed(2)}`);
  console.log(`  Total HAHA cost: $${januaryCost.toFixed(2)}`);
  console.log(`  HAHA margin: ${(((januaryRevenue - januaryCost) / januaryRevenue) * 100).toFixed(1)}%`);

  return transactions;
}

// Parse NAYAX CSV properly (handles multi-line quoted fields)
function parseNAYAXCSV(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');

  // Skip "Table 1" and empty line, get header at line 2
  const headerLine = lines[2];
  const headers = headerLine.split(',').map(h => h.trim());

  const records = [];
  let currentRecord = [];
  let inQuotes = false;
  let currentField = '';

  // Start from line 3 (first data row)
  for (let lineNum = 3; lineNum < lines.length; lineNum++) {
    const line = lines[lineNum];

    for (let i = 0; i < line.length; i++) {
      const char = line[i];

      if (char === '"') {
        inQuotes = !inQuotes;
        currentField += char;
      } else if (char === ',' && !inQuotes) {
        currentRecord.push(currentField.trim());
        currentField = '';
      } else {
        currentField += char;
      }
    }

    // If not in quotes, we've finished this record
    if (!inQuotes) {
      currentRecord.push(currentField.trim());
      currentField = '';

      // Complete record found
      if (currentRecord.length === headers.length) {
        const record = {};
        headers.forEach((header, idx) => {
          record[header] = currentRecord[idx];
        });
        records.push(record);
      }

      currentRecord = [];
    } else {
      // Still in multi-line quoted field, add newline
      currentField += '\n';
    }
  }

  return records;
}

// Process NAYAX Transactions (with proper multi-line handling and cost mapping)
function processNAYAXTransactions(nayaxMap) {
  console.log('\n=== Processing NAYAX Transactions ===');
  const filePath = path.join(RAW_DIR, NAYAX_FILE);
  const nayaxData = parseNAYAXCSV(filePath);

  console.log(`  Raw NAYAX records parsed: ${nayaxData.length}`);

  const transactions = [];
  let januaryCount = 0;
  let januaryRevenue = 0;
  let januaryCost = 0;
  let cashRevenue = 0;

  nayaxData.forEach(row => {
    const settlementTime = row['Machine Settlement Time']?.trim() || '';
    if (!settlementTime) return;

    const date = parseDate(settlementTime);
    if (!isJanuary2026(date)) return;

    const machineName = row['Machine Name']?.trim() || 'Unknown';
    const settlementValue = row['Settlement Value (Vend Price)']?.trim() || '0';
    const productInfo = row['Product Selection Info']?.replace(/"/g, '').trim() || '';
    const paymentMethod = row['Payment Method (Source)']?.trim() || '';

    const revenue = parseFloat(settlementValue.replace(/[$,]/g, '')) || 0;
    if (revenue === 0) return; // Skip zero-value transactions

    // Extract product name (first line of product info, before parentheses)
    const productName = productInfo.split('\n')[0].split('(')[0].trim();

    // Get cost from SKU map
    const skuInfo = nayaxMap[productName];
    const cost = skuInfo?.cost || 0;
    const profit = revenue - cost;
    const marginPercent = revenue > 0 ? (profit / revenue * 100) : 0;

    // Track cash transactions for specific locations
    if (paymentMethod === 'Cash' &&
        (machineName.includes('CP Rec Center') ||
         machineName.includes('Strictly Soda') ||
         machineName.includes('HL Chapman') ||
         machineName.includes('Chapman'))) {
      cashRevenue += revenue;
    }

    transactions.push({
      date,
      location: machineName,
      Master_SKU: skuInfo?.Master_SKU || 'NAYAX',
      Master_Name: skuInfo?.Master_Name || productName,
      Product_Family: skuInfo?.Product_Family || 'NAYAX',
      revenue,
      cost,
      quantity: 1,
      profit,
      gross_margin_percent: marginPercent
    });

    januaryCount++;
    januaryRevenue += revenue;
    januaryCost += cost;
  });

  console.log(`  Processed ${januaryCount} NAYAX transactions`);
  console.log(`  Total NAYAX revenue: $${januaryRevenue.toFixed(2)}`);
  console.log(`  Total NAYAX cost: $${januaryCost.toFixed(2)}`);
  console.log(`  NAYAX margin: ${januaryRevenue > 0 ? (((januaryRevenue - januaryCost) / januaryRevenue) * 100).toFixed(1) : 0}%`);
  console.log(`  Cash transactions (CP/Strictly/Chapman): $${cashRevenue.toFixed(2)}`);

  return transactions;
}

// Process USAT/Cantaloup Transactions (Ryder and Strictly Cedar Park)
function processUSATTransactions(cantaloupeMap) {
  console.log('\n=== Processing USAT/Cantaloup Transactions ===');
  const filePath = path.join(RAW_DIR, USAT_FILE);

  try {
    // Parse USAT file manually since product name is in an unnamed column
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.trim().split('\n');

    const transactions = [];
    let januaryCount = 0;
    let januaryRevenue = 0;
    let januaryCost = 0;
    let matchedProducts = 0;

    // Start from line 4 (after "Table 1", "Transaction Log", date range, and header)
    for (let i = 4; i < lines.length; i++) {
      const parts = lines[i].split(',');
      if (parts.length < 9) continue;

      const timestamp = parts[0]?.trim();
      if (!timestamp) continue;

      const date = timestamp.split(' ')[0];
      if (!isJanuary2026(date)) continue;

      const location = parts[1]?.trim() || 'Unknown';
      const productName = parts[3]?.trim() || ''; // Column 4 (index 3) has the product name!
      const total = parseFloat(parts[7]?.replace(/[$,]/g, '')) || 0;

      if (total === 0 || !productName) continue;

      // Get SKU mapping cost
      const skuInfo = cantaloupeMap[productName];
      const cost = skuInfo?.cost || 0;

      if (skuInfo) matchedProducts++;

      const profit = total - cost;
      const marginPercent = total > 0 ? (profit / total * 100) : 0;

      transactions.push({
        date,
        location,
        Master_SKU: skuInfo?.Master_SKU || 'USAT',
        Master_Name: skuInfo?.Master_Name || productName,
        Product_Family: skuInfo?.Product_Family || 'USAT',
        revenue: total,
        cost,
        quantity: 1,
        profit,
        gross_margin_percent: marginPercent
      });

      januaryCount++;
      januaryRevenue += total;
      januaryCost += cost;
    }

    console.log(`  Processed ${januaryCount} USAT transactions`);
    console.log(`  Matched products: ${matchedProducts}/${januaryCount} (${((matchedProducts/januaryCount)*100).toFixed(1)}%)`);
    console.log(`  Total USAT revenue: $${januaryRevenue.toFixed(2)}`);
    console.log(`  Total USAT cost: $${januaryCost.toFixed(2)}`);
    console.log(`  USAT margin: ${januaryRevenue > 0 ? (((januaryRevenue - januaryCost) / januaryRevenue) * 100).toFixed(1) : 0}%`);

    return transactions;
  } catch (error) {
    console.warn(`  Warning: Could not process USAT file: ${error.message}`);
    return [];
  }
}

// Generate master_dashboard_data.csv
function generateMasterFile(transactions) {
  console.log('\n=== Generating Master Dashboard Data ===');

  const outputPath = path.join(PROCESSED_DIR, 'master_dashboard_data.csv');
  const headers = ['date', 'location', 'Master_SKU', 'Master_Name', 'Product_Family',
                   'revenue', 'cost', 'quantity', 'profit', 'gross_margin_percent'];

  let csv = headers.join(',') + '\n';

  transactions.forEach(t => {
    csv += [
      t.date,
      t.location,
      t.Master_SKU,
      `"${t.Master_Name.replace(/"/g, '""')}"`, // Escape quotes
      t.Product_Family,
      t.revenue.toFixed(2),
      t.cost.toFixed(2),
      t.quantity.toFixed(1),
      t.profit.toFixed(2),
      t.gross_margin_percent.toFixed(1)
    ].join(',') + '\n';
  });

  fs.writeFileSync(outputPath, csv);
  console.log(`  ✓ Saved to: ${outputPath}`);

  // Calculate totals
  const totalRevenue = transactions.reduce((sum, t) => sum + t.revenue, 0);
  const totalProfit = transactions.reduce((sum, t) => sum + t.profit, 0);
  const totalTransactions = transactions.length;

  console.log(`\n=== SUMMARY ===`);
  console.log(`  Total transactions: ${totalTransactions}`);
  console.log(`  Total revenue: $${totalRevenue.toFixed(2)}`);
  console.log(`  Total profit: $${totalProfit.toFixed(2)}`);
  console.log(`  Expected revenue: $23,461.67`);
  console.log(`  Difference: $${(23461.67 - totalRevenue).toFixed(2)}`);

  return outputPath;
}

// Main execution
async function main() {
  try {
    console.log('=== DASHBOARD DATA PROCESSOR ===');
    console.log('Processing January 2026 data...\n');

    // Ensure processed directory exists
    if (!fs.existsSync(PROCESSED_DIR)) {
      fs.mkdirSync(PROCESSED_DIR, { recursive: true });
    }

    // Load mappings
    const locationMap = loadLocationMapping();
    const { hahaMap, nayaxMap, cantaloupeMap } = loadSKUMapping();
    console.log(`  Loaded ${Object.keys(locationMap).length} location mappings`);
    console.log(`  Loaded ${Object.keys(hahaMap).length} HAHA SKU mappings`);
    console.log(`  Loaded ${Object.keys(nayaxMap).length} NAYAX SKU mappings`);
    console.log(`  Loaded ${Object.keys(cantaloupeMap).length} Cantaloupe SKU mappings`);

    // Process all data sources
    const hahaTransactions = processHAHAProducts(locationMap, hahaMap);
    const nayaxTransactions = processNAYAXTransactions(nayaxMap);
    const usatTransactions = processUSATTransactions(cantaloupeMap);

    // Combine all transactions
    const allTransactions = [...hahaTransactions, ...nayaxTransactions, ...usatTransactions];

    // Generate master file
    const outputPath = generateMasterFile(allTransactions);

    console.log('\n✓ Processing complete!');
    console.log(`\nNext step: Update page.tsx to use: data/processed/master_dashboard_data.csv`);

  } catch (error) {
    console.error('ERROR:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();
