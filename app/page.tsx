import { readFileSync } from "fs";
import { join } from "path";
import DashboardClient from "./DashboardClient";

export interface Transaction {
  date: string;
  location: string;
  Master_SKU: string;
  Master_Name: string;
  Product_Family: string;
  revenue: number;
  cost: number;
  quantity: number;
  profit: number;
  gross_margin_percent: number;
}

function parseCSV(filePath: string): Transaction[] {
  const fileContent = readFileSync(filePath, "utf-8");
  const lines = fileContent.trim().split("\n");

  return lines.slice(1).map((line) => {
    const values = line.split(",");
    return {
      date: values[0],
      location: values[1],
      Master_SKU: values[2],
      Master_Name: values[3],
      Product_Family: values[4],
      revenue: parseFloat(values[5]) || 0,
      cost: parseFloat(values[6]) || 0,
      quantity: parseFloat(values[7]) || 0,
      profit: parseFloat(values[8]) || 0,
      gross_margin_percent: parseFloat(values[9]) || 0,
    };
  });
}

export default function Dashboard() {
  const csvPath = join(process.cwd(), "data/processed/master_dashboard_data.csv");
  const transactions = parseCSV(csvPath);

  // Get unique locations
  const locations = Array.from(new Set(transactions.map(t => t.location))).sort();

  return <DashboardClient transactions={transactions} locations={locations} />;
}
