"use client";

import { useState, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ComposedChart,
  Line,
  Legend,
  LabelList,
  ScatterChart,
  Scatter,
  ZAxis,
  ReferenceLine,
} from "recharts";
import { DollarSign, Package, Layers, Filter, X, Calendar, Upload, Settings } from "lucide-react";
import Link from "next/link";
import { Transaction } from "./page";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import "./datepicker-dark.css";

interface DashboardClientProps {
  transactions: Transaction[];
  locations: string[];
}

type DatePreset = "today" | "yesterday" | "thisWeek" | "lastWeek" | "thisMonth" | "lastMonth" | "custom";

export default function DashboardClient({ transactions, locations }: DashboardClientProps) {
  console.log("=== DASHBOARD CLIENT DEBUG ===");
  console.log("Total transactions received:", transactions.length);
  console.log("Sample transaction:", transactions[0]);
  console.log("Total locations:", locations.length);
  console.log("Locations list:", locations);

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedLocations, setSelectedLocations] = useState<Set<string>>(new Set(locations));
  const [datePreset, setDatePreset] = useState<DatePreset>("lastMonth"); // Changed from "thisWeek" to "lastMonth" to match January data
  const [customStartDate, setCustomStartDate] = useState("");
  const [customEndDate, setCustomEndDate] = useState("");

  // Calculate date range based on preset
  const getDateRange = (): { start: Date; end: Date } => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    switch (datePreset) {
      case "today":
        return { start: today, end: today };
      case "yesterday":
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        return { start: yesterday, end: yesterday };
      case "thisWeek":
        const thisWeekStart = new Date(today);
        thisWeekStart.setDate(today.getDate() - today.getDay());
        return { start: thisWeekStart, end: today };
      case "lastWeek":
        const lastWeekEnd = new Date(today);
        lastWeekEnd.setDate(today.getDate() - today.getDay() - 1);
        const lastWeekStart = new Date(lastWeekEnd);
        lastWeekStart.setDate(lastWeekEnd.getDate() - 6);
        return { start: lastWeekStart, end: lastWeekEnd };
      case "thisMonth":
        const thisMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);
        return { start: thisMonthStart, end: today };
      case "lastMonth":
        const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
        return { start: lastMonthStart, end: lastMonthEnd };
      case "custom":
        if (customStartDate && customEndDate) {
          return {
            start: new Date(customStartDate),
            end: new Date(customEndDate),
          };
        }
        return { start: today, end: today };
      default:
        return { start: today, end: today };
    }
  };

  const dateRange = getDateRange();

  // Filter transactions based on selected locations and date range
  const filteredTransactions = useMemo(() => {
    console.log("=== FILTERING TRANSACTIONS ===");
    console.log("Date range:", dateRange.start, "to", dateRange.end);
    console.log("Selected locations count:", selectedLocations.size);

    const filtered = transactions.filter((t) => {
      const txDate = new Date(t.date);
      const inDateRange = txDate >= dateRange.start && txDate <= dateRange.end;
      const inSelectedLocations = selectedLocations.has(t.location);
      return inDateRange && inSelectedLocations;
    });

    console.log("Filtered transactions:", filtered.length);
    console.log("Sample filtered transaction:", filtered[0]);
    return filtered;
  }, [transactions, selectedLocations, dateRange]);

  // Calculate stats from filtered data
  const stats = useMemo(() => {
    const totalRevenue = filteredTransactions.reduce((sum, t) => sum + t.revenue, 0);
    const totalProfit = filteredTransactions.reduce((sum, t) => sum + t.profit, 0);
    const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue * 100) : 0;
    const totalQuantity = filteredTransactions.reduce((sum, t) => sum + t.quantity, 0);

    return [
      {
        title: "Total Revenue",
        value: `$${totalRevenue.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}`,
        description: "Filtered sales",
      },
      {
        title: "Total Profit",
        value: `$${totalProfit.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}`,
        description: `${avgMargin.toFixed(1)}% margin`,
      },
      {
        title: "Units Sold",
        value: totalQuantity.toLocaleString(),
        description: "Total items",
      },
    ];
  }, [filteredTransactions]);

  // Calculate revenue by location
  const locationRevenue = useMemo(() => {
    console.log("=== CALCULATING LOCATION REVENUE ===");
    const revenueByLoc: Record<string, number> = {};
    filteredTransactions.forEach((t) => {
      revenueByLoc[t.location] = (revenueByLoc[t.location] || 0) + t.revenue;
    });

    console.log("Revenue by location (raw):", revenueByLoc);

    const result = Object.entries(revenueByLoc)
      .map(([location, revenue]) => ({
        location,
        revenue: Math.round(revenue * 100) / 100,
      }))
      .sort((a, b) => b.revenue - a.revenue);

    console.log("Location revenue array for chart:", result);
    console.log("Chart will show", result.length, "bars");
    return result;
  }, [filteredTransactions]);

  // Calculate profit and margin by location
  const locationProfitMargin = useMemo(() => {
    console.log("=== CALCULATING LOCATION PROFIT & MARGIN ===");
    const profitByLoc: Record<string, number> = {};
    const revenueByLoc: Record<string, number> = {};

    filteredTransactions.forEach((t) => {
      profitByLoc[t.location] = (profitByLoc[t.location] || 0) + t.profit;
      revenueByLoc[t.location] = (revenueByLoc[t.location] || 0) + t.revenue;
    });

    const result = Object.entries(profitByLoc)
      .map(([location, profit]) => {
        const revenue = revenueByLoc[location];
        const marginPercent = revenue > 0 ? (profit / revenue * 100) : 0;
        return {
          location,
          profit: Math.round(profit * 100) / 100,
          marginPercent: Math.round(marginPercent * 10) / 10,
        };
      })
      .sort((a, b) => b.profit - a.profit);

    console.log("Location profit & margin array for chart:", result);
    return result;
  }, [filteredTransactions]);

  // Calculate top products by revenue
  const topProductsByRevenue = useMemo(() => {
    console.log("=== CALCULATING TOP PRODUCTS BY REVENUE ===");
    const productData: Record<string, { revenue: number; quantity: number }> = {};

    filteredTransactions.forEach((t) => {
      const productName = t.Master_Name.replace(/^"|"$/g, ''); // Remove surrounding quotes
      if (!productData[productName]) {
        productData[productName] = { revenue: 0, quantity: 0 };
      }
      productData[productName].revenue += t.revenue;
      productData[productName].quantity += t.quantity;
    });

    const result = Object.entries(productData)
      .map(([product, data]) => ({
        product,
        revenue: Math.round(data.revenue * 100) / 100,
        quantity: data.quantity,
      }))
      .sort((a, b) => b.revenue - a.revenue)
      .slice(0, 15);

    console.log("Top 15 products by revenue:", result);
    return result;
  }, [filteredTransactions]);

  // Calculate top products by average margin
  const topProductsByMargin = useMemo(() => {
    console.log("=== CALCULATING TOP PRODUCTS BY MARGIN ===");
    const productData: Record<string, { revenue: number; profit: number; cost: number; count: number }> = {};

    filteredTransactions.forEach((t) => {
      const productName = t.Master_Name.replace(/^"|"$/g, ''); // Remove surrounding quotes
      if (!productData[productName]) {
        productData[productName] = { revenue: 0, profit: 0, cost: 0, count: 0 };
      }
      productData[productName].revenue += t.revenue;
      productData[productName].profit += t.profit;
      productData[productName].cost += t.cost;
      productData[productName].count += 1;
    });

    const result = Object.entries(productData)
      .map(([product, data]) => {
        const avgMargin = data.revenue > 0 ? (data.profit / data.revenue * 100) : 0;
        return {
          product,
          margin: Math.round(avgMargin * 10) / 10,
          revenue: Math.round(data.revenue * 100) / 100,
          cost: Math.round(data.cost * 100) / 100,
          count: data.count,
        };
      })
      .filter(p => p.count >= 5 && p.cost > 0) // Only include products with 5+ transactions AND cost data
      .sort((a, b) => b.margin - a.margin)
      .slice(0, 15);

    console.log("Top 15 products by margin (with costs):", result);
    return result;
  }, [filteredTransactions]);

  // Product Performance Scatter Data
  const productPerformanceData = useMemo(() => {
    console.log("=== CALCULATING PRODUCT PERFORMANCE SCATTER DATA ===");
    const productData: Record<string, {
      name: string;
      revenue: number;
      quantity: number;
      profit: number;
      sku: string;
    }> = {};

    filteredTransactions.forEach((t) => {
      const sku = t.Master_SKU;
      if (!productData[sku]) {
        productData[sku] = {
          name: t.Master_Name.replace(/^"|"$/g, ''),
          revenue: 0,
          quantity: 0,
          profit: 0,
          sku: sku,
        };
      }
      productData[sku].revenue += t.revenue;
      productData[sku].quantity += t.quantity;
      productData[sku].profit += t.profit;
    });

    const scatterData = Object.values(productData)
      .filter(p => p.quantity >= 5) // Exclude slow-movers
      .map(p => ({
        name: p.name,
        totalRevenue: Math.round(p.revenue * 100) / 100,
        totalQuantity: Math.round(p.quantity),
        totalProfit: Math.round(p.profit * 100) / 100,
        profitMargin: p.revenue > 0 ? Math.round((p.profit / p.revenue) * 100 * 10) / 10 : 0,
        avgPrice: p.quantity > 0 ? Math.round((p.revenue / p.quantity) * 100) / 100 : 0,
      }));

    console.log("Product performance scatter data:", scatterData);
    return scatterData;
  }, [filteredTransactions]);

  // Calculate average values for reference lines
  const avgQuantity = useMemo(() => {
    if (productPerformanceData.length === 0) return 0;
    const sum = productPerformanceData.reduce((acc, p) => acc + p.totalQuantity, 0);
    return Math.round(sum / productPerformanceData.length);
  }, [productPerformanceData]);

  const avgRevenue = useMemo(() => {
    if (productPerformanceData.length === 0) return 0;
    const sum = productPerformanceData.reduce((acc, p) => acc + p.totalRevenue, 0);
    return Math.round(sum / productPerformanceData.length * 100) / 100;
  }, [productPerformanceData]);

  // Category Efficiency Data (Gross Margin % by Product Type)
  const categoryEfficiencyData = useMemo(() => {
    console.log("=== CALCULATING CATEGORY EFFICIENCY ===");
    const typeData: Record<string, { revenue: number; cost: number; profit: number }> = {};

    filteredTransactions.forEach((t) => {
      const type = t.Type || "Unknown";
      if (!typeData[type]) {
        typeData[type] = { revenue: 0, cost: 0, profit: 0 };
      }
      typeData[type].revenue += t.revenue;
      typeData[type].cost += t.cost * t.quantity;
      typeData[type].profit += t.profit;
    });

    const result = Object.entries(typeData)
      .map(([type, data]) => {
        const grossMargin = data.revenue > 0 ? (data.profit / data.revenue * 100) : 0;
        return {
          type,
          grossMargin: Math.round(grossMargin * 10) / 10,
          revenue: Math.round(data.revenue * 100) / 100,
          profit: Math.round(data.profit * 100) / 100,
        };
      })
      .filter(c => c.revenue >= 100) // Filter out categories with <$100 revenue
      .sort((a, b) => b.grossMargin - a.grossMargin);

    console.log("Category efficiency data:", result);
    return result;
  }, [filteredTransactions]);

  // Location Yield Metrics (Profit per Swipe by Location)
  const locationYieldData = useMemo(() => {
    console.log("=== CALCULATING LOCATION YIELD ===");
    const locationData: Record<string, { profit: number; transactionCount: number }> = {};

    filteredTransactions.forEach((t) => {
      const loc = t.location;
      if (!locationData[loc]) {
        locationData[loc] = { profit: 0, transactionCount: 0 };
      }
      locationData[loc].profit += t.profit;
      locationData[loc].transactionCount += 1;
    });

    const result = Object.entries(locationData)
      .map(([location, data]) => {
        const profitPerSwipe = data.transactionCount > 0 ? data.profit / data.transactionCount : 0;
        return {
          location,
          profitPerSwipe: Math.round(profitPerSwipe * 100) / 100,
          totalProfit: Math.round(data.profit * 100) / 100,
          transactionCount: data.transactionCount,
        };
      })
      .sort((a, b) => b.profitPerSwipe - a.profitPerSwipe);

    console.log("Location yield data:", result);
    return result;
  }, [filteredTransactions]);

  // COGS Trendline Data (Cost of Goods Sold % over time)
  const cogsTrendData = useMemo(() => {
    console.log("=== CALCULATING COGS TREND ===");
    const monthlyData: Record<string, { revenue: number; cogs: number }> = {};

    filteredTransactions.forEach((t) => {
      const month = t.date.substring(0, 7); // YYYY-MM
      if (!monthlyData[month]) {
        monthlyData[month] = { revenue: 0, cogs: 0 };
      }
      monthlyData[month].revenue += t.revenue;
      monthlyData[month].cogs += t.cost * t.quantity;
    });

    const result = Object.entries(monthlyData)
      .map(([month, data]) => {
        const cogsPercent = data.revenue > 0 ? (data.cogs / data.revenue * 100) : 0;
        return {
          month,
          cogsPercent: Math.round(cogsPercent * 10) / 10,
          revenue: Math.round(data.revenue * 100) / 100,
          cogs: Math.round(data.cogs * 100) / 100,
        };
      })
      .sort((a, b) => a.month.localeCompare(b.month));

    console.log("COGS trend data:", result);
    return result;
  }, [filteredTransactions]);


  // Location filter handlers
  const toggleLocation = (location: string) => {
    const newSelected = new Set(selectedLocations);
    if (newSelected.has(location)) {
      newSelected.delete(location);
    } else {
      newSelected.add(location);
    }
    setSelectedLocations(newSelected);
  };

  const selectAllLocations = () => setSelectedLocations(new Set(locations));
  const clearAllLocations = () => setSelectedLocations(new Set());

  // Format date range display
  const formatDateRange = () => {
    const options: Intl.DateTimeFormatOptions = { month: "short", day: "numeric", year: "numeric" };
    return `${dateRange.start.toLocaleDateString("en-US", options)} - ${dateRange.end.toLocaleDateString("en-US", options)}`;
  };

  const iconMap: Record<string, typeof DollarSign> = {
    "Total Revenue": DollarSign,
    "Total Profit": DollarSign,
    "Units Sold": Package,
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Sidebar for location filter */}
      <div
        className={`fixed left-0 top-0 h-full w-80 bg-[#0a0a0a] border-r border-[#222] z-50 transform transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Filter className="w-5 h-5 text-[#09fe94]" />
              Filter Locations
            </h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 hover:bg-[#222] rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="mb-4 text-sm text-gray-400">
            {selectedLocations.size} of {locations.length} locations selected
          </div>

          <div className="flex gap-2 mb-4">
            <button
              onClick={selectAllLocations}
              className="flex-1 px-3 py-2 bg-[#1a237e] hover:bg-[#283593] rounded-lg text-sm transition-colors"
            >
              Select All
            </button>
            <button
              onClick={clearAllLocations}
              className="flex-1 px-3 py-2 bg-[#111] hover:bg-[#222] border border-[#333] rounded-lg text-sm transition-colors"
            >
              Clear All
            </button>
          </div>

          <div className="space-y-2 max-h-[calc(100vh-250px)] overflow-y-auto">
            {locations.map((location) => (
              <label
                key={location}
                className="flex items-center gap-3 p-3 hover:bg-[#111] rounded-lg cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selectedLocations.has(location)}
                  onChange={() => toggleLocation(location)}
                  className="w-4 h-4 accent-[#09fe94]"
                />
                <span className="text-sm">{location}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Overlay when sidebar is open */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <main className="p-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 mb-2">
              <img
                src="/logo.svg"
                alt="Smart Vending ATX Logo"
                className="h-12 w-auto"
              />
              <div>
                <h1 className="text-4xl font-bold tracking-tight">
                  Dashboard
                </h1>
                <p className="text-gray-400">Real-time analytics dashboard</p>
              </div>
            </div>

            {/* Admin Navigation Buttons */}
            <div className="flex gap-3">
              <Link
                href="/admin/upload"
                className="px-4 py-2 bg-[#09fe94]/10 text-[#09fe94] rounded-lg hover:bg-[#09fe94]/20 transition-colors border border-[#09fe94]/30 flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Upload Data
              </Link>
              <Link
                href="/admin/sku-mappings"
                className="px-4 py-2 bg-[#09fe94]/10 text-[#09fe94] rounded-lg hover:bg-[#09fe94]/20 transition-colors border border-[#09fe94]/30 flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                SKU Mappings
              </Link>
            </div>
          </div>
        </header>

        {/* Filter Controls */}
        <div className="mb-8 space-y-4">
          {/* Date Range Filter */}
          <div className="bg-[#111] border border-[#222] rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="w-5 h-5 text-[#09fe94]" />
              <h3 className="text-lg font-semibold">Date Range</h3>
            </div>

            <div className="flex flex-wrap gap-2 mb-4">
              {[
                { label: "Today", value: "today" },
                { label: "Yesterday", value: "yesterday" },
                { label: "This Week", value: "thisWeek" },
                { label: "Last Week", value: "lastWeek" },
                { label: "This Month", value: "thisMonth" },
                { label: "Last Month", value: "lastMonth" },
                { label: "Custom", value: "custom" },
              ].map((preset) => (
                <button
                  key={preset.value}
                  onClick={() => setDatePreset(preset.value as DatePreset)}
                  className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                    datePreset === preset.value
                      ? "bg-[#1a237e] text-white"
                      : "bg-[#0a0a0a] hover:bg-[#222] text-gray-400"
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>

            {datePreset === "custom" && (
              <div className="flex gap-4 mb-4">
                <div className="flex-1">
                  <label className="block text-sm text-gray-400 mb-2">Start Date</label>
                  <DatePicker
                    selected={customStartDate ? new Date(customStartDate) : null}
                    onChange={(date: Date | null) => {
                      if (date) {
                        setCustomStartDate(date.toISOString().split('T')[0]);
                      }
                    }}
                    dateFormat="MMM d, yyyy"
                    className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white"
                    calendarClassName="dark-calendar"
                    placeholderText="Select start date"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-sm text-gray-400 mb-2">End Date</label>
                  <DatePicker
                    selected={customEndDate ? new Date(customEndDate) : null}
                    onChange={(date: Date | null) => {
                      if (date) {
                        setCustomEndDate(date.toISOString().split('T')[0]);
                      }
                    }}
                    dateFormat="MMM d, yyyy"
                    className="w-full px-4 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white"
                    calendarClassName="dark-calendar"
                    placeholderText="Select end date"
                    minDate={customStartDate ? new Date(customStartDate) : undefined}
                  />
                </div>
              </div>
            )}

            <div className="text-sm text-[#09fe94]">
              Showing data for: {formatDateRange()}
            </div>
          </div>

          {/* Location Filter Button */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="w-full bg-[#111] border border-[#222] hover:border-[#09fe94]/30 rounded-2xl p-6 text-left transition-colors flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <Filter className="w-5 h-5 text-[#09fe94]" />
              <div>
                <h3 className="text-lg font-semibold mb-1">Location Filter</h3>
                <p className="text-sm text-gray-400">
                  {selectedLocations.size} of {locations.length} locations selected
                </p>
              </div>
            </div>
            <div className="text-gray-400">›</div>
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {stats.map((stat) => {
            const Icon = iconMap[stat.title] || Package;
            return (
              <div
                key={stat.title}
                className="bg-[#111] border border-[#222] rounded-2xl p-6 hover:border-[#09fe94]/30 transition-colors"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-gray-400 text-sm font-medium">
                    {stat.title}
                  </span>
                  <div className="w-10 h-10 rounded-xl bg-[#09fe94]/10 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-[#09fe94]" />
                  </div>
                </div>
                <div className="text-3xl font-bold text-white mb-1">
                  {stat.value}
                </div>
                <p className="text-gray-500 text-sm">{stat.description}</p>
              </div>
            );
          })}
        </div>

        {/* Revenue by Location Chart */}
        {locationRevenue.length > 0 ? (
          <div className="bg-[#111] border border-[#222] rounded-2xl p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-white">
                  Revenue by Location
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Top performing locations by revenue
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#09fe94]"></span>
                <span className="text-gray-400 text-sm">Revenue ($)</span>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={700}>
                <BarChart
                  layout="vertical"
                  data={locationRevenue}
                  margin={{ top: 5, right: 30, left: 160, bottom: 20 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#222"
                    vertical={false}
                  />
                  <XAxis
                    type="number"
                    stroke="#666"
                    tick={{ fill: "#888", fontSize: 12 }}
                    axisLine={{ stroke: "#333" }}
                    tickFormatter={(value) => `$${value.toLocaleString()}`}
                  />
                  <YAxis
                    type="category"
                    dataKey="location"
                    stroke="#666"
                    interval={0}
                    width={150}
                    axisLine={{ stroke: "#333" }}
                    tick={{ fill: "#E5E7EB", fontSize: 11, textAnchor: "end" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a1a1a",
                      border: "1px solid #333",
                      borderRadius: "12px",
                      boxShadow: "0 4px 20px rgba(118, 255, 3, 0.1)",
                    }}
                    labelStyle={{ color: "#fff", fontWeight: 600 }}
                    itemStyle={{ color: "#09fe94" }}
                    formatter={(value: number | undefined) => value !== undefined ? [`$${value.toFixed(2)}`, "Revenue"] : ["$0.00", "Revenue"]}
                  />
                  <Bar
                    dataKey="revenue"
                    fill="#09fe94"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
          </div>
        ) : (
          <div className="bg-[#111] border border-[#222] rounded-2xl p-12 text-center mb-8">
            <p className="text-gray-400 text-lg">
              No data available for the selected filters
            </p>
            <p className="text-gray-500 text-sm mt-2">
              Try adjusting your date range or location selections
            </p>
          </div>
        )}

        {/* Profit by Location + Margin % Chart */}
        {locationProfitMargin.length > 0 && (
          <div className="bg-[#111] border border-[#222] rounded-2xl p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-white">
                  Profit by Location + Margin %
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Shows which locations are actually profitable
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#09fe94]"></span>
                  <span className="text-gray-400 text-sm">Profit ($)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#ffffff]"></span>
                  <span className="text-gray-400 text-sm">Margin (%)</span>
                </div>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={600}>
              <ComposedChart
                data={locationProfitMargin}
                margin={{ top: 20, right: 80, left: 60, bottom: 120 }}
                barCategoryGap="5%"
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#222"
                  horizontal={true}
                  vertical={false}
                />
                <XAxis
                  type="category"
                  dataKey="location"
                  stroke="#666"
                  interval={0}
                  height={100}
                  axisLine={{ stroke: "#333" }}
                  tick={(props: any) => {
                    const { x, y, payload } = props;
                    return (
                      <g transform={`translate(${x},${y})`}>
                        <text
                          x={0}
                          y={0}
                          dy={10}
                          textAnchor="start"
                          fill="#E5E7EB"
                          fontSize={10}
                          transform="rotate(90)"
                        >
                          {payload.value}
                        </text>
                      </g>
                    );
                  }}
                />
                <YAxis
                  yAxisId="left"
                  type="number"
                  stroke="#666"
                  tick={{ fill: "#888", fontSize: 12 }}
                  axisLine={{ stroke: "#333" }}
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                />
                <YAxis
                  yAxisId="right"
                  type="number"
                  orientation="right"
                  stroke="#ffffff"
                  tick={{ fill: "#ffffff", fontSize: 12 }}
                  axisLine={{ stroke: "#ffffff" }}
                  domain={[0, 100]}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a1a1a",
                    border: "1px solid #333",
                    borderRadius: "12px",
                    boxShadow: "0 4px 20px rgba(118, 255, 3, 0.1)",
                  }}
                  labelStyle={{ color: "#fff", fontWeight: 600 }}
                  formatter={(value: number | undefined, name: string | undefined) => {
                    if (value === undefined) return ["N/A", name || ""];
                    if (name === "profit") return [`$${value.toFixed(2)}`, "Profit"];
                    if (name === "marginPercent") return [`${value.toFixed(1)}%`, "Margin"];
                    return [value, name || ""];
                  }}
                />
                <Bar
                  dataKey="profit"
                  fill="#09fe94"
                  radius={[4, 4, 0, 0]}
                  yAxisId="left"
                />
                <Line
                  type="monotone"
                  dataKey="marginPercent"
                  stroke="#ffffff"
                  strokeWidth={2}
                  dot={{ fill: "#ffffff", r: 4 }}
                  yAxisId="right"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Product Performance Scatter Chart */}
        {productPerformanceData.length > 0 && (
          <div className="bg-[#111] border border-[#222] rounded-2xl p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-white">
                  Product Performance Analysis
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Volume vs Revenue with Margin Insight (5+ units sold)
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#09fe94]"></span>
                  <span className="text-gray-400 text-sm">&gt;70% Margin</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#27a162]"></span>
                  <span className="text-gray-400 text-sm">50-70% Margin</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#267449]"></span>
                  <span className="text-gray-400 text-sm">&lt;50% Margin</span>
                </div>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={500}>
              <ScatterChart margin={{ top: 20, right: 80, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                <XAxis
                  type="number"
                  dataKey="totalQuantity"
                  name="Volume"
                  stroke="#666"
                  tick={{ fill: "#888", fontSize: 12 }}
                  axisLine={{ stroke: "#333" }}
                  label={{ value: "Units Sold", position: "insideBottom", offset: -10, fill: "#888" }}
                />
                <YAxis
                  type="number"
                  dataKey="totalRevenue"
                  name="Revenue"
                  stroke="#666"
                  tick={{ fill: "#888", fontSize: 12 }}
                  axisLine={{ stroke: "#333" }}
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                  label={{ value: "Revenue ($)", angle: -90, position: "insideLeft", fill: "#888" }}
                />
                <ZAxis
                  type="number"
                  dataKey="profitMargin"
                  range={[60, 400]}
                  name="Margin"
                />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3", stroke: "#09fe94" }}
                  contentStyle={{
                    backgroundColor: "#1a1a1a",
                    border: "1px solid #333",
                    borderRadius: "12px",
                    boxShadow: "0 4px 20px rgba(9, 254, 148, 0.1)",
                  }}
                  labelStyle={{ color: "#fff", fontWeight: 600 }}
                  content={({ payload }) => {
                    if (!payload || payload.length === 0) return null;
                    const data = payload[0].payload;
                    return (
                      <div className="bg-[#1a1a1a] border border-[#333] rounded-xl p-4 shadow-lg">
                        <p className="text-white font-bold mb-2">{data.name}</p>
                        <div className="space-y-1 text-sm">
                          <p className="text-gray-300">
                            <span className="text-gray-400">Revenue:</span> ${data.totalRevenue.toLocaleString()}
                          </p>
                          <p className="text-gray-300">
                            <span className="text-gray-400">Units Sold:</span> {data.totalQuantity}
                          </p>
                          <p className="text-gray-300">
                            <span className="text-gray-400">Avg Price:</span> ${data.avgPrice}
                          </p>
                          <p className="text-gray-300">
                            <span className="text-gray-400">Margin:</span> {data.profitMargin}%
                          </p>
                        </div>
                      </div>
                    );
                  }}
                />
                <ReferenceLine
                  x={avgQuantity}
                  stroke="#666"
                  strokeDasharray="5 5"
                  strokeWidth={1}
                  label={{ value: "Avg Volume", position: "top", fill: "#888", fontSize: 11 }}
                />
                <ReferenceLine
                  y={avgRevenue}
                  stroke="#666"
                  strokeDasharray="5 5"
                  strokeWidth={1}
                  label={{ value: "Avg Revenue", position: "right", fill: "#888", fontSize: 11 }}
                />
                <Scatter name="Products" data={productPerformanceData}>
                  {productPerformanceData.map((entry, index) => {
                    let fill = "#267449"; // < 50%
                    if (entry.profitMargin > 70) {
                      fill = "#09fe94"; // > 70%
                    } else if (entry.profitMargin >= 50) {
                      fill = "#27a162"; // 50-70%
                    }
                    return <Cell key={`cell-${index}`} fill={fill} />;
                  })}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Top Products Charts - Side by Side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8 mt-8">
          {/* Top 15 Products by Revenue */}
          {topProductsByRevenue.length > 0 && (
            <div className="bg-[#111] border border-[#222] rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-white">
                    Top 15 Products by Revenue
                  </h2>
                  <p className="text-gray-400 text-sm mt-1">
                    Best selling products by total sales
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#09fe94]"></span>
                  <span className="text-gray-400 text-sm">Revenue ($)</span>
                </div>
              </div>

              <ResponsiveContainer width="100%" height={500}>
                <BarChart
                  layout="vertical"
                  data={topProductsByRevenue}
                  margin={{ top: 5, right: 30, left: 20, bottom: 20 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#222"
                    vertical={false}
                  />
                  <XAxis
                    type="number"
                    stroke="#666"
                    tick={{ fill: "#888", fontSize: 12 }}
                    axisLine={{ stroke: "#333" }}
                    tickFormatter={(value) => `$${value.toLocaleString()}`}
                  />
                  <YAxis
                    type="category"
                    dataKey="product"
                    stroke="#666"
                    interval={0}
                    width={180}
                    axisLine={{ stroke: "#333" }}
                    tick={{ fill: "#E5E7EB", fontSize: 11, textAnchor: "end" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a1a1a",
                      border: "1px solid #333",
                      borderRadius: "12px",
                      boxShadow: "0 4px 20px rgba(118, 255, 3, 0.1)",
                    }}
                    labelStyle={{ color: "#fff", fontWeight: 600 }}
                    formatter={(value: number | undefined, name: string | undefined) => {
                      if (name === "revenue") return [`$${value?.toFixed(2)}`, "Revenue"];
                      return [value, name || ""];
                    }}
                  />
                  <Bar
                    dataKey="revenue"
                    fill="#09fe94"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top 15 Products by Average Margin */}
          {topProductsByMargin.length > 0 && (
            <div className="bg-[#111] border border-[#222] rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-white">
                    Top 15 Products by Margin %
                  </h2>
                  <p className="text-gray-400 text-sm mt-1">
                    Most profitable products by margin (5+ sales)
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#ffffff]"></span>
                  <span className="text-gray-400 text-sm">Margin (%)</span>
                </div>
              </div>

              <ResponsiveContainer width="100%" height={500}>
                <BarChart
                  layout="vertical"
                  data={topProductsByMargin}
                  margin={{ top: 5, right: 30, left: 20, bottom: 20 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#222"
                    vertical={false}
                  />
                  <XAxis
                    type="number"
                    stroke="#666"
                    tick={{ fill: "#888", fontSize: 12 }}
                    axisLine={{ stroke: "#333" }}
                    tickFormatter={(value) => `${value}%`}
                    domain={[60, 100]}
                    ticks={[60, 70, 80, 90, 100]}
                  />
                  <YAxis
                    type="category"
                    dataKey="product"
                    stroke="#666"
                    interval={0}
                    width={180}
                    axisLine={{ stroke: "#333" }}
                    tick={{ fill: "#E5E7EB", fontSize: 11, textAnchor: "end" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a1a1a",
                      border: "1px solid #333",
                      borderRadius: "12px",
                      boxShadow: "0 4px 20px rgba(118, 255, 3, 0.1)",
                    }}
                    labelStyle={{ color: "#fff", fontWeight: 600 }}
                    formatter={(value: number | undefined, name: string | undefined) => {
                      if (name === "margin") return [`${value?.toFixed(1)}%`, "Margin"];
                      return [value, name || ""];
                    }}
                  />
                  <Bar
                    dataKey="margin"
                    fill="#ffffff"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Category Efficiency Chart */}
        {categoryEfficiencyData.length > 0 && (
          <div className="bg-[#111] border border-[#222] rounded-2xl p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-white">
                  Category Efficiency
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Gross margin % by product type
                </p>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                layout="vertical"
                data={categoryEfficiencyData}
                margin={{ top: 5, right: 30, left: 20, bottom: 20 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#222"
                  horizontal={false}
                />
                <XAxis
                  type="number"
                  stroke="#666"
                  tick={{ fill: "#888", fontSize: 12 }}
                  axisLine={{ stroke: "#333" }}
                  tickFormatter={(value) => `${value}%`}
                />
                <YAxis
                  type="category"
                  dataKey="type"
                  stroke="#666"
                  interval={0}
                  width={150}
                  axisLine={{ stroke: "#333" }}
                  tick={{ fill: "#E5E7EB", fontSize: 11, textAnchor: "end" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a1a1a",
                    border: "1px solid #333",
                    borderRadius: "12px",
                    boxShadow: "0 4px 20px rgba(118, 255, 3, 0.1)",
                  }}
                  labelStyle={{ color: "#fff", fontWeight: 600 }}
                  formatter={(value: number | undefined) => value !== undefined ? [`${value}%`, "Gross Margin"] : ["-", "Gross Margin"]}
                />
                <Bar dataKey="grossMargin" radius={[0, 4, 4, 0]}>
                  {categoryEfficiencyData.map((entry, index) => {
                    let fill = "#dc2626"; // < 45%
                    if (entry.grossMargin > 60) {
                      fill = "#09fe94"; // > 60%
                    } else if (entry.grossMargin >= 45) {
                      fill = "#27a162"; // 45-60%
                    }
                    return <Cell key={`cell-${index}`} fill={fill} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Location Yield Metrics */}
        {locationYieldData.length > 0 && (
          <div className="bg-[#111] border border-[#222] rounded-2xl p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-white">
                  Location Yield
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Profit per swipe by location
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#333]">
                    <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Location</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium text-sm">Profit/Swipe</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium text-sm">Total Profit</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium text-sm">Transactions</th>
                  </tr>
                </thead>
                <tbody>
                  {locationYieldData.map((location, index) => (
                    <tr
                      key={index}
                      className="border-b border-[#222] hover:bg-[#1a1a1a] transition-colors"
                    >
                      <td className="py-3 px-4 text-white">{location.location}</td>
                      <td className="py-3 px-4 text-right font-semibold text-[#09fe94]">
                        ${location.profitPerSwipe.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-300">
                        ${location.totalProfit.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-400">
                        {location.transactionCount.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* COGS Trendline */}
        {cogsTrendData.length > 1 && (
          <div className="bg-[#111] border border-[#222] rounded-2xl p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-white">
                  COGS Trendline
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Cost of goods sold % over time
                </p>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart
                data={cogsTrendData}
                margin={{ top: 5, right: 30, left: 20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                <XAxis
                  dataKey="month"
                  stroke="#666"
                  tick={{ fill: "#888", fontSize: 12 }}
                  axisLine={{ stroke: "#333" }}
                />
                <YAxis
                  stroke="#666"
                  tick={{ fill: "#888", fontSize: 12 }}
                  axisLine={{ stroke: "#333" }}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a1a1a",
                    border: "1px solid #333",
                    borderRadius: "12px",
                    boxShadow: "0 4px 20px rgba(118, 255, 3, 0.1)",
                  }}
                  labelStyle={{ color: "#fff", fontWeight: 600 }}
                  formatter={(value: number | undefined, name: string | undefined) => {
                    if (value === undefined) return ["-", name || ""];
                    if (name === "cogsPercent") return [`${value}%`, "COGS %"];
                    return [value, name];
                  }}
                />
                <Legend />
                <ReferenceLine
                  y={40}
                  stroke="#666"
                  strokeDasharray="5 5"
                  label={{ value: "Target COGS (40%)", position: "right", fill: "#888", fontSize: 11 }}
                />
                <Line
                  type="monotone"
                  dataKey="cogsPercent"
                  stroke="#09fe94"
                  strokeWidth={2}
                  dot={{ fill: "#09fe94", r: 4 }}
                  name="COGS %"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}


        {/* Footer */}
        <footer className="mt-10 text-center text-gray-500 text-sm">
          <p>
            Powered by <span className="text-[#09fe94]">LowrCarbon</span>{" "}
            aesthetic • Smart Vending ATX © 2026
          </p>
        </footer>
      </main>
    </div>
  );
}
