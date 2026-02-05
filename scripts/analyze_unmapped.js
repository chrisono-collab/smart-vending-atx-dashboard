const fs = require('fs');
const path = require('path');

// Read unmapped products
const unmappedFile = path.join(__dirname, '../unmapped_products_report.csv');
const unmappedContent = fs.readFileSync(unmappedFile, 'utf-8');
const unmappedLines = unmappedContent.trim().split('\n').slice(1); // Skip header

// Read SKU map
const skuMapFile = path.join(__dirname, '../Product SKU Map.csv');
const skuMapContent = fs.readFileSync(skuMapFile, 'utf-8');
const skuMapLines = skuMapContent.trim().split('\n').slice(1); // Skip header

// Parse SKU map to get all Nayax names
const existingNayaxNames = new Set();
const skuMapByName = {};
skuMapLines.forEach(line => {
  const match = line.match(/^([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]*),([^,]*),([^,]*)$/);
  if (match) {
    const masterSKU = match[1];
    const masterName = match[2];
    const nayaxName = match[7]?.trim();
    const cost = match[4];

    if (nayaxName) {
      existingNayaxNames.add(nayaxName);
    }
    skuMapByName[masterName] = { masterSKU, cost, nayaxName };
  }
});

console.log('=== UNMAPPED PRODUCTS ANALYSIS ===\n');

const needsNayaxColumn = [];
const needsNewRow = [];
const unknown = [];

unmappedLines.forEach(line => {
  const match = line.match(/^"([^"]+)",([^,]+),/);
  if (match) {
    const productName = match[1];
    const sku = match[2];

    if (sku === 'SKU0353' || sku.startsWith('SKU')) {
      unknown.push(productName);
      return;
    }

    // Check if similar product exists in SKU map
    const similarProduct = Object.entries(skuMapByName).find(([name, info]) => {
      const normalized1 = name.toLowerCase().replace(/[^a-z0-9]/g, '');
      const normalized2 = productName.toLowerCase().replace(/[^a-z0-9]/g, '');
      return normalized1.includes(normalized2) || normalized2.includes(normalized1);
    });

    if (similarProduct) {
      needsNayaxColumn.push({
        nayaxName: productName,
        existingProduct: similarProduct[0],
        masterSKU: similarProduct[1].masterSKU,
        cost: similarProduct[1].cost
      });
    } else {
      needsNewRow.push(productName);
    }
  }
});

console.log('A) Products that EXIST in SKU Map - just add to Nayax_Name column (column G):');
console.log(`   (${needsNayaxColumn.length} products)\n`);
needsNayaxColumn.forEach(p => {
  console.log(`   "${p.nayaxName}" → Add to row with "${p.existingProduct}" (${p.masterSKU})`);
});

console.log(`\n\nB) Products that DON'T EXIST - need new rows with Master_SKU, Cost, etc:`);
console.log(`   (${needsNewRow.length} products)\n`);
needsNewRow.forEach(p => {
  console.log(`   "${p}"`);
});

console.log(`\n\nC) Unknown/Special cases - need manual review:`);
console.log(`   (${unknown.length} products)\n`);
unknown.forEach(p => {
  console.log(`   "${p}"`);
});

console.log('\n=== INSTRUCTIONS ===');
console.log('For group A: Open Product SKU Map.csv, find the row, add the NAYAX name to column G');
console.log('For group B: Add new rows with all details (Master_SKU, Master_Name, Product_Family, Cost, Nayax_Name)');
console.log('For group C: Investigate what these products are and handle accordingly');
