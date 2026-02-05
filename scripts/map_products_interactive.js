const fs = require('fs');
const path = require('path');
const readline = require('readline');

const SKU_MAP_FILE = path.join(__dirname, '../data/raw/Product SKU Map.csv');
const MASTER_FILE = path.join(__dirname, '../data/processed/master_dashboard_data.csv');

// Create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(query) {
  return new Promise(resolve => rl.question(query, resolve));
}

function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current);
  return result;
}

function normalizeForMatch(str) {
  if (!str) return '';
  return str.toLowerCase()
    .replace(/[^a-z0-9]/g, '')
    .replace(/\s+/g, '');
}

function findSimilarProducts(productName, skuMapData) {
  const normalized = normalizeForMatch(productName);
  const matches = [];

  skuMapData.forEach(row => {
    const masterName = row.masterName;
    if (!masterName) return;
    const normalizedMaster = normalizeForMatch(masterName);

    // Check if names are very similar
    if (normalizedMaster.includes(normalized) ||
        normalized.includes(normalizedMaster) ||
        levenshteinDistance(normalized, normalizedMaster) <= 3) {
      matches.push({
        masterSKU: row.masterSKU,
        masterName: row.masterName,
        productFamily: row.productFamily,
        cost: row.cost,
        hahaName: row.hahaName,
        nayaxName: row.nayaxName,
        cantaloupeName: row.cantaloupeName
      });
    }
  });

  return matches;
}

function levenshteinDistance(str1, str2) {
  const matrix = [];

  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }

  return matrix[str2.length][str1.length];
}

async function main() {
  console.log('=== INTERACTIVE PRODUCT MAPPER ===\n');

  // Load unmapped products
  const masterContent = fs.readFileSync(MASTER_FILE, 'utf-8');
  const masterLines = masterContent.trim().split('\n').slice(1);

  const unmappedProducts = {};
  masterLines.forEach(line => {
    const parts = line.split(',');
    const productName = parts[3]?.replace(/^"|"$/g, '');
    const revenue = parseFloat(parts[5]) || 0;
    const cost = parseFloat(parts[6]) || 0;
    const sku = parts[2];

    if (cost === 0 && revenue > 0) {
      const key = `${productName}|||${sku}`;
      if (!unmappedProducts[key]) {
        unmappedProducts[key] = { productName, sku, revenue: 0, transactions: 0 };
      }
      unmappedProducts[key].revenue += revenue;
      unmappedProducts[key].transactions += 1;
    }
  });

  const sortedUnmapped = Object.values(unmappedProducts)
    .sort((a, b) => b.revenue - a.revenue);

  console.log(`Found ${sortedUnmapped.length} unmapped products\n`);

  // Load SKU map
  const skuMapContent = fs.readFileSync(SKU_MAP_FILE, 'utf-8');
  const skuMapLines = skuMapContent.trim().split('\n');
  const skuMapHeader = skuMapLines[0];
  const skuMapData = [];

  skuMapLines.slice(1).forEach(line => {
    const values = parseCSVLine(line);
    if (values[0]) {
      skuMapData.push({
        masterSKU: values[0]?.trim(),
        masterName: values[1]?.trim(),
        productFamily: values[2]?.trim(),
        cost: values[3]?.trim(),
        status: values[4]?.trim(),
        hahaName: values[5]?.trim(),
        nayaxName: values[6]?.trim(),
        cantaloupeName: values[7]?.trim(),
        rawLine: line
      });
    }
  });

  let updatedRows = 0;
  let newRows = 0;
  const newEntries = [];

  // Process each unmapped product
  for (const data of sortedUnmapped) {
    const productName = data.productName;
    const sku = data.sku;

    console.log('\n' + '='.repeat(70));
    console.log(`Product: ${productName}`);
    console.log(`Current SKU: ${sku}`);
    console.log(`Revenue: $${data.revenue.toFixed(2)} (${data.transactions} sales)`);
    console.log('='.repeat(70));

    // If product has existing SKU (not NAYAX), just update cost
    if (sku !== 'NAYAX') {
      const existingRow = skuMapData.find(r => r.masterSKU === sku);
      if (existingRow) {
        console.log(`\nThis product exists as ${sku} but has $0 cost.`);
        const cost = await question('Enter cost (e.g., 1.50): $');
        if (cost) {
          existingRow.cost = '$' + parseFloat(cost).toFixed(2);
          console.log(`✓ Will update ${sku} cost to $${cost}`);
          updatedRows++;
        }
        continue;
      }
    }

    // Find similar products
    const similar = findSimilarProducts(productName, skuMapData);

    if (similar.length > 0) {
      console.log('\nFound similar products in SKU map:');
      similar.forEach((match, idx) => {
        console.log(`  ${idx + 1}. ${match.masterName} (${match.masterSKU}) - Cost: ${match.cost}`);
        if (match.nayaxName) console.log(`     Current Nayax Name: "${match.nayaxName}"`);
      });

      const choice = await question('\nOptions: [1-' + similar.length + '] to select match, [n] for new product, [s] to skip: ');

      if (choice.toLowerCase() === 's') {
        console.log('Skipped.');
        continue;
      } else if (choice.toLowerCase() === 'n') {
        // Create new product
        const cost = await question('Enter cost (e.g., 1.50): $');
        const family = await question('Enter product family (or press Enter to use product name): ');

        const nextSKU = 'SKU' + String(Math.max(...skuMapData.map(r => {
          const num = parseInt(r.masterSKU.replace('SKU', ''));
          return isNaN(num) ? 0 : num;
        })) + 1).padStart(4, '0');

        newEntries.push({
          masterSKU: nextSKU,
          masterName: productName,
          productFamily: family || productName,
          cost: '$' + parseFloat(cost).toFixed(2),
          status: 'Mapped',
          hahaName: '',
          nayaxName: productName,
          cantaloupeName: ''
        });

        console.log(`✓ Will create new product: ${nextSKU} - ${productName} at $${cost}`);
        newRows++;
      } else {
        const idx = parseInt(choice) - 1;
        if (idx >= 0 && idx < similar.length) {
          const selectedMatch = similar[idx];

          // Find the row in skuMapData and update it
          const rowIndex = skuMapData.findIndex(r => r.masterSKU === selectedMatch.masterSKU);
          if (rowIndex !== -1) {
            skuMapData[rowIndex].nayaxName = productName;
            console.log(`✓ Will update ${selectedMatch.masterSKU} - adding "${productName}" to Nayax_Name column`);
            updatedRows++;
          }
        }
      }
    } else {
      console.log('\nNo similar products found.');
      const choice = await question('Options: [n] to create new product, [s] to skip: ');

      if (choice.toLowerCase() === 'n') {
        const cost = await question('Enter cost (e.g., 1.50): $');
        const family = await question('Enter product family (or press Enter to use product name): ');

        const nextSKU = 'SKU' + String(Math.max(...skuMapData.map(r => {
          const num = parseInt(r.masterSKU.replace('SKU', ''));
          return isNaN(num) ? 0 : num;
        })) + 1).padStart(4, '0');

        newEntries.push({
          masterSKU: nextSKU,
          masterName: productName,
          productFamily: family || productName,
          cost: '$' + parseFloat(cost).toFixed(2),
          status: 'Mapped',
          hahaName: '',
          nayaxName: productName,
          cantaloupeName: ''
        });

        console.log(`✓ Will create new product: ${nextSKU} - ${productName} at $${cost}`);
        newRows++;
      }
    }
  }

  console.log('\n\n' + '='.repeat(70));
  console.log('SUMMARY');
  console.log('='.repeat(70));
  console.log(`Existing products updated: ${updatedRows}`);
  console.log(`New products to add: ${newRows}`);
  console.log(`Total changes: ${updatedRows + newRows}`);

  if (updatedRows + newRows === 0) {
    console.log('\nNo changes to save.');
    rl.close();
    return;
  }

  const confirm = await question('\nSave changes to Product SKU Map.csv? [y/n]: ');

  if (confirm.toLowerCase() === 'y') {
    // Rebuild CSV
    const newCSVLines = [skuMapHeader];

    skuMapData.forEach(row => {
      const line = `${row.masterSKU},${row.masterName},${row.productFamily},${row.cost},${row.status},${row.hahaName},${row.nayaxName},${row.cantaloupeName}`;
      newCSVLines.push(line);
    });

    // Add new entries
    newEntries.forEach(entry => {
      const line = `${entry.masterSKU},${entry.masterName},${entry.productFamily},${entry.cost},${entry.status},${entry.hahaName},${entry.nayaxName},${entry.cantaloupeName}`;
      newCSVLines.push(line);
    });

    fs.writeFileSync(SKU_MAP_FILE, newCSVLines.join('\n'));
    console.log('\n✓ Product SKU Map.csv updated!');

    const reprocess = await question('\nReprocess data now? [y/n]: ');
    if (reprocess.toLowerCase() === 'y') {
      rl.close();
      console.log('\nReprocessing data...\n');
      const { execSync } = require('child_process');
      execSync('node ' + path.join(__dirname, 'process_data.js'), { stdio: 'inherit' });
    } else {
      console.log('\nRun "node scripts/process_data.js" when ready to reprocess.');
      rl.close();
    }
  } else {
    console.log('\nChanges discarded.');
    rl.close();
  }
}

main().catch(err => {
  console.error('Error:', err);
  rl.close();
  process.exit(1);
});
