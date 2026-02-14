"use client";

import { useState, useEffect } from "react";
import { Upload, Download, RefreshCw, Plus } from "lucide-react";
import Link from "next/link";

interface SKUMapping {
  master_sku: string;
  master_name: string;
  product_family: string | null;
  type: string | null;
  cost: number;
  cantaloupe_name: string | null;
  haha_ai_name: string | null;
  nayax_name: string | null;
}

interface UploadResult {
  success: boolean;
  totalSKUs?: number;
  cantaloupeMappings?: number;
  hahaAIMappings?: number;
  nayaxMappings?: number;
  updated?: number;
  error?: string;
}

export default function SKUMappingsPage() {
  const [skus, setSKUs] = useState<SKUMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchSKUs();
  }, []);

  const fetchSKUs = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_SUPABASE_URL}/rest/v1/sku_mappings?order=master_sku.asc`,
        {
          headers: {
            apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
            Authorization: `Bearer ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}`,
          },
        }
      );
      const data = await response.json();
      setSKUs(data);
    } catch (error) {
      console.error("Error fetching SKUs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/sku-mappings/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        setUploadResult({
          success: true,
          ...data,
        });
        // Refresh SKU list
        fetchSKUs();
      } else {
        setUploadResult({
          success: false,
          error: data.error || "Upload failed",
        });
      }
    } catch (error: any) {
      setUploadResult({
        success: false,
        error: error.message || "Upload failed",
      });
    } finally {
      setUploading(false);
    }
  };

  const filteredSKUs = skus.filter(
    (sku) =>
      sku.master_sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sku.master_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sku.cantaloupe_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sku.type?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="border-b border-[#222] bg-black sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-[#09fe94]">SKU Mappings</h1>
              <p className="text-gray-400 text-sm mt-1">
                Manage product mappings • {skus.length} total SKUs
              </p>
            </div>
            <div className="flex gap-3">
              <Link
                href="/admin/upload"
                className="px-4 py-2 bg-[#111] border border-[#333] text-white rounded-lg hover:bg-[#1a1a1a] transition-colors"
              >
                Upload Transactions
              </Link>
              <Link
                href="/"
                className="px-4 py-2 bg-[#09fe94]/10 text-[#09fe94] rounded-lg hover:bg-[#09fe94]/20 transition-colors border border-[#09fe94]/30"
              >
                ← Back to Dashboard
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Upload Section */}
        <div className="bg-[#111] border border-[#222] rounded-2xl p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold">Upload Updated SKU Mapping</h2>
              <p className="text-gray-400 text-sm mt-1">
                Upload your Excel file to update all SKU mappings
              </p>
            </div>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileUpload}
              className="hidden"
              id="skuFileInput"
            />
            <label
              htmlFor="skuFileInput"
              className={`px-6 py-3 rounded-lg font-semibold flex items-center gap-2 transition-colors cursor-pointer ${
                uploading
                  ? "bg-gray-600 cursor-not-allowed"
                  : "bg-[#09fe94] text-black hover:bg-[#07cc75]"
              }`}
            >
              {uploading ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  Upload Excel File
                </>
              )}
            </label>
          </div>

          {/* Upload Result */}
          {uploadResult && (
            <div
              className={`mt-4 p-4 rounded-lg ${
                uploadResult.success
                  ? "bg-green-500/10 border border-green-500/30"
                  : "bg-red-500/10 border border-red-500/30"
              }`}
            >
              {uploadResult.success ? (
                <div>
                  <p className="text-green-400 font-semibold mb-2">
                    ✓ SKU mappings updated successfully!
                  </p>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Total SKUs:</span>
                      <span className="ml-2 text-white font-semibold">
                        {uploadResult.totalSKUs}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Cantaloupe:</span>
                      <span className="ml-2 text-white font-semibold">
                        {uploadResult.cantaloupeMappings}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Haha AI:</span>
                      <span className="ml-2 text-white font-semibold">
                        {uploadResult.hahaAIMappings}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Nayax:</span>
                      <span className="ml-2 text-white font-semibold">
                        {uploadResult.nayaxMappings}
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-red-300">{uploadResult.error}</p>
              )}
            </div>
          )}
        </div>

        {/* Search and Stats */}
        <div className="flex items-center justify-between mb-6">
          <input
            type="text"
            placeholder="Search SKUs, products, or types..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-4 py-2 bg-[#111] border border-[#333] rounded-lg text-white w-96 focus:outline-none focus:border-[#09fe94]"
          />
          <button
            onClick={fetchSKUs}
            className="px-4 py-2 bg-[#111] border border-[#333] text-white rounded-lg hover:bg-[#1a1a1a] transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* SKU Table */}
        <div className="bg-[#111] border border-[#222] rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[#0a0a0a] border-b border-[#222]">
                <tr>
                  <th className="text-left py-4 px-4 text-gray-400 font-medium text-sm">
                    Master SKU
                  </th>
                  <th className="text-left py-4 px-4 text-gray-400 font-medium text-sm">
                    Master Name
                  </th>
                  <th className="text-left py-4 px-4 text-gray-400 font-medium text-sm">
                    Type
                  </th>
                  <th className="text-right py-4 px-4 text-gray-400 font-medium text-sm">
                    Cost
                  </th>
                  <th className="text-left py-4 px-4 text-gray-400 font-medium text-sm">
                    Cantaloupe Name
                  </th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-gray-400">
                      Loading...
                    </td>
                  </tr>
                ) : filteredSKUs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-gray-400">
                      No SKUs found
                    </td>
                  </tr>
                ) : (
                  filteredSKUs.map((sku) => (
                    <tr
                      key={sku.master_sku}
                      className="border-b border-[#222] hover:bg-[#1a1a1a] transition-colors"
                    >
                      <td className="py-3 px-4 font-mono text-sm text-[#09fe94]">
                        {sku.master_sku}
                      </td>
                      <td className="py-3 px-4 text-white">{sku.master_name}</td>
                      <td className="py-3 px-4 text-gray-300 text-sm">
                        {sku.type || "-"}
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-white">
                        ${sku.cost.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-gray-400 text-sm">
                        {sku.cantaloupe_name || "-"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-[#111] border border-[#222] rounded-2xl p-6">
          <h3 className="text-lg font-semibold mb-4">💡 How to Update SKU Mappings</h3>
          <ol className="space-y-2 text-gray-300">
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">1.</span>
              <span>
                Open your SKU Mapping Excel file (e.g., "SKU Mapping with Cost.xlsx")
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">2.</span>
              <span>
                Add new products or update existing ones (cost, type, mappings)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">3.</span>
              <span>Save the Excel file</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">4.</span>
              <span>
                Click "Upload Excel File" above and select your updated file
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">5.</span>
              <span>
                Future transaction uploads will automatically use the new mappings
              </span>
            </li>
          </ol>
        </div>
      </main>
    </div>
  );
}
