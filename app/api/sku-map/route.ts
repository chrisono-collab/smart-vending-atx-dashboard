import { NextRequest, NextResponse } from "next/server";
import { readFileSync, writeFileSync } from "fs";
import { join } from "path";
import { execSync } from "child_process";

interface UnmappedProduct {
  productName: string;
  sku: string;
  revenue: number;
  transactions: number;
}

interface Mapping {
  unmappedProduct: UnmappedProduct;
  action: "match" | "new";
  matchedSKU?: string;
  newCost?: string;
  newFamily?: string;
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

export async function POST(request: NextRequest) {
  try {
    const { mappings } = await request.json() as { mappings: Mapping[] };

    if (!mappings || mappings.length === 0) {
      return NextResponse.json({ error: "No mappings provided" }, { status: 400 });
    }

    const SKU_MAP_FILE = join(process.cwd(), "data/raw/Product SKU Map.csv");

    // Read existing SKU map
    const content = readFileSync(SKU_MAP_FILE, "utf-8");
    const lines = content.trim().split("\n");
    const header = lines[0];

    const skuMapData: SKUMapEntry[] = lines.slice(1).map(line => {
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

    let updatedCount = 0;
    let addedCount = 0;

    // Process mappings
    for (const mapping of mappings) {
      const { unmappedProduct, action, matchedSKU, newCost, newFamily } = mapping;

      if (action === "match" && matchedSKU) {
        // Find and update existing product
        const entry = skuMapData.find(e => e.masterSKU === matchedSKU);
        if (entry) {
          if (unmappedProduct.sku === "NAYAX") {
            entry.nayaxName = unmappedProduct.productName;
          } else if (unmappedProduct.sku.startsWith("SKU")) {
            // Update cost for existing SKU
            if (newCost) {
              entry.cost = "$" + parseFloat(newCost).toFixed(2);
            }
          }
          updatedCount++;
        }
      } else if (action === "new" && newCost) {
        // Check if updating existing SKU's cost
        if (unmappedProduct.sku.startsWith("SKU")) {
          const entry = skuMapData.find(e => e.masterSKU === unmappedProduct.sku);
          if (entry) {
            entry.cost = "$" + parseFloat(newCost).toFixed(2);
            updatedCount++;
            continue;
          }
        }

        // Create new product
        const nextSKUNum = Math.max(
          ...skuMapData.map(e => {
            const num = parseInt(e.masterSKU.replace("SKU", ""));
            return isNaN(num) ? 0 : num;
          })
        ) + 1;

        const nextSKU = "SKU" + String(nextSKUNum).padStart(4, "0");

        skuMapData.push({
          masterSKU: nextSKU,
          masterName: unmappedProduct.productName,
          productFamily: newFamily || unmappedProduct.productName,
          cost: "$" + parseFloat(newCost).toFixed(2),
          status: "Mapped",
          hahaName: "",
          nayaxName: unmappedProduct.sku === "NAYAX" ? unmappedProduct.productName : "",
          cantaloupeName: "",
        });

        addedCount++;
      }
    }

    // Write updated SKU map
    const newCSVLines = [header];
    skuMapData.forEach(entry => {
      newCSVLines.push(
        `${entry.masterSKU},${entry.masterName},${entry.productFamily},${entry.cost},${entry.status},${entry.hahaName},${entry.nayaxName},${entry.cantaloupeName}`
      );
    });

    writeFileSync(SKU_MAP_FILE, newCSVLines.join("\n"));

    // Reprocess data
    const scriptPath = join(process.cwd(), "scripts/process_data.js");
    execSync(`node "${scriptPath}"`, { cwd: process.cwd() });

    return NextResponse.json({
      success: true,
      updated: updatedCount,
      added: addedCount,
    });
  } catch (error) {
    console.error("Error processing mappings:", error);
    return NextResponse.json(
      { error: String(error) },
      { status: 500 }
    );
  }
}
