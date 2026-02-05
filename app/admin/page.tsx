import { readFileSync } from "fs";
import { join } from "path";
import AdminClient from "./AdminClient";

export const dynamic = 'force-dynamic';

interface UnmappedProduct {
  productName: string;
  sku: string;
  revenue: number;
  transactions: number;
}

interface SKUMapEntry {
  masterSKU: string;
  masterName: string;
  productFamily: string;
  cost: string;
  status: string;
  hahaName: string;
  nayaxName: string;
  cantaloupeName: string;
}

function parseCSVLine(line: string): string[] {
  const result: string[] = [];
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

function getUnmappedProducts(): UnmappedProduct[] {
  try {
    const masterFile = join(process.cwd(), "data/processed/master_dashboard_data.csv");
    const content = readFileSync(masterFile, "utf-8");
    const lines = content.trim().split("\n").slice(1);

    const unmappedMap: Record<string, UnmappedProduct> = {};

    lines.forEach(line => {
      const parts = line.split(",");
      const productName = parts[3]?.replace(/^"|"$/g, "") || "";
      const revenue = parseFloat(parts[5]) || 0;
      const cost = parseFloat(parts[6]) || 0;
      const sku = parts[2] || "";

      if (cost === 0 && revenue > 0) {
        const key = `${productName}|||${sku}`;
        if (!unmappedMap[key]) {
          unmappedMap[key] = { productName, sku, revenue: 0, transactions: 0 };
        }
        unmappedMap[key].revenue += revenue;
        unmappedMap[key].transactions += 1;
      }
    });

    // Filter out known issues and samples
    const excludedSKUs = ["SKU0353", "SKU0127", "SKU0318"]; // Unknown (NAYAX error), Flock (sample), Steel Omni (sample)

    return Object.values(unmappedMap)
      .filter(p => !excludedSKUs.includes(p.sku))
      .sort((a, b) => b.revenue - a.revenue);
  } catch (error) {
    console.error("Error loading unmapped products:", error);
    return [];
  }
}

function getSKUMap(): SKUMapEntry[] {
  try {
    const skuMapFile = join(process.cwd(), "data/raw/Product SKU Map.csv");
    const content = readFileSync(skuMapFile, "utf-8");
    const lines = content.trim().split("\n").slice(1);

    return lines.map(line => {
      const values = parseCSVLine(line);
      return {
        masterSKU: values[0]?.trim() || "",
        masterName: values[1]?.trim() || "",
        productFamily: values[2]?.trim() || "",
        cost: values[3]?.trim() || "$0",
        status: values[4]?.trim() || "",
        hahaName: values[5]?.trim() || "",
        nayaxName: values[6]?.trim() || "",
        cantaloupeName: values[7]?.trim() || "",
      };
    }).filter(entry => entry.masterSKU);
  } catch (error) {
    console.error("Error loading SKU map:", error);
    return [];
  }
}

export default function AdminPage() {
  const unmappedProducts = getUnmappedProducts();
  const skuMap = getSKUMap();

  return <AdminClient unmappedProducts={unmappedProducts} skuMap={skuMap} />;
}
