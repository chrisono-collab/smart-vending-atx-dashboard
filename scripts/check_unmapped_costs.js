const fs = require('fs');
const path = require('path');

const masterFile = path.join(__dirname, '../data/processed/master_dashboard_data.csv');
const content = fs.readFileSync(masterFile, 'utf-8');
const lines = content.trim().split('\n');

const productsWithZeroCost = {};

for (let i = 1; i < lines.length; i++) {
  const parts = lines[i].split(',');
  const productName = parts[3]?.replace(/^"|"$/g, '');
  const revenue = parseFloat(parts[5]) || 0;
  const cost = parseFloat(parts[6]) || 0;
  const sku = parts[2];

  if (cost === 0 && revenue > 0) {
    if (!productsWithZeroCost[productName]) {
      productsWithZeroCost[productName] = { revenue: 0, transactions: 0, sku };
    }
    productsWithZeroCost[productName].revenue += revenue;
    productsWithZeroCost[productName].transactions += 1;
  }
}

const sorted = Object.entries(productsWithZeroCost)
  .sort((a, b) => b[1].revenue - a[1].revenue);

console.log('=== PRODUCTS WITH MISSING COST DATA (January 2026) ===\n');
console.log('Total products with $0 cost:', sorted.length);
console.log('Total revenue impacted: $' + sorted.reduce((sum, [_, data]) => sum + data.revenue, 0).toFixed(2));
console.log('\nTop 20 by Revenue:\n');

sorted.slice(0, 20).forEach(([product, data], idx) => {
  console.log(`${(idx + 1).toString().padStart(2)}. ${product.padEnd(45)} $${data.revenue.toFixed(2).padStart(8)} (${data.transactions} sales) [${data.sku}]`);
});

// Save full report
const reportLines = ['Product Name,SKU,Revenue,Transactions'];
sorted.forEach(([product, data]) => {
  reportLines.push(`"${product}",${data.sku},${data.revenue.toFixed(2)},${data.transactions}`);
});

const reportPath = path.join(__dirname, '../unmapped_products_report.csv');
fs.writeFileSync(reportPath, reportLines.join('\n'));
console.log('\n✓ Full report saved to: unmapped_products_report.csv');
console.log('\n=== HOW TO UPDATE COSTS ===');
console.log('1. Open: Product SKU Map.csv');
console.log('2. Find the product name in the appropriate column:');
console.log('   - Haha_AI_Name (column F) for HAHA products');
console.log('   - Nayax_Name (column G) for NAYAX products');
console.log('   - Cantaloupe_Name (column H) for USAT products');
console.log('3. Update the Cost column (column D) with the actual cost');
console.log('4. Rerun: node scripts/process_data.js');
console.log('5. Dashboard will automatically reload with updated margins!');
