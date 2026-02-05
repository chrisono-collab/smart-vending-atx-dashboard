"use client";

import { useState, useMemo } from "react";

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

interface Mapping {
  unmappedProduct: UnmappedProduct;
  action: "match" | "new" | "skip";
  matchedSKU?: string;
  newCost?: string;
  newFamily?: string;
}

export default function AdminClient({
  unmappedProducts,
  skuMap,
}: {
  unmappedProducts: UnmappedProduct[];
  skuMap: SKUMapEntry[];
}) {
  const [mappings, setMappings] = useState<Record<string, Mapping>>({});
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProduct, setSelectedProduct] = useState<UnmappedProduct | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState<string | null>(null);

  const normalizeForMatch = (str: string) => {
    return str.toLowerCase().replace(/[^a-z0-9]/g, "");
  };

  const findSimilarProducts = (productName: string) => {
    const normalized = normalizeForMatch(productName);
    return skuMap
      .filter(entry => {
        const normalizedMaster = normalizeForMatch(entry.masterName);
        return (
          normalizedMaster.includes(normalized) ||
          normalized.includes(normalizedMaster)
        );
      })
      .slice(0, 5);
  };

  const selectedSuggestions = useMemo(() => {
    if (!selectedProduct) return [];
    return findSimilarProducts(selectedProduct.productName);
  }, [selectedProduct, skuMap]);

  const filteredSKUMap = useMemo(() => {
    if (!searchTerm) return skuMap.slice(0, 50);
    const normalized = normalizeForMatch(searchTerm);
    return skuMap
      .filter(entry => normalizeForMatch(entry.masterName).includes(normalized))
      .slice(0, 50);
  }, [searchTerm, skuMap]);

  const handleSelectMatch = (unmapped: UnmappedProduct, matchedSKU: string) => {
    const key = `${unmapped.productName}|||${unmapped.sku}`;
    setMappings({
      ...mappings,
      [key]: {
        unmappedProduct: unmapped,
        action: "match",
        matchedSKU,
      },
    });
  };

  const handleCreateNew = (unmapped: UnmappedProduct, cost: string, family: string) => {
    const key = `${unmapped.productName}|||${unmapped.sku}`;
    setMappings({
      ...mappings,
      [key]: {
        unmappedProduct: unmapped,
        action: "new",
        newCost: cost,
        newFamily: family || unmapped.productName,
      },
    });
  };

  const handleSkip = (unmapped: UnmappedProduct) => {
    const key = `${unmapped.productName}|||${unmapped.sku}`;
    const newMappings = { ...mappings };
    delete newMappings[key];
    setMappings(newMappings);
    if (selectedProduct?.productName === unmapped.productName) {
      setSelectedProduct(null);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveResult(null);

    try {
      const response = await fetch("/api/sku-map", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mappings: Object.values(mappings) }),
      });

      const result = await response.json();

      if (response.ok) {
        setSaveResult(`✓ Success! Updated ${result.updated} products, added ${result.added} new products.`);
        setTimeout(() => window.location.reload(), 2000);
      } else {
        setSaveResult(`✗ Error: ${result.error}`);
      }
    } catch (error) {
      setSaveResult(`✗ Error: ${error}`);
    } finally {
      setSaving(false);
    }
  };

  const totalMappings = Object.keys(mappings).length;
  const totalRevenue = unmappedProducts.reduce((sum, p) => sum + p.revenue, 0);
  const mappedRevenue = Object.values(mappings).reduce(
    (sum, m) => sum + m.unmappedProduct.revenue,
    0
  );

  return (
    <div className="min-h-screen bg-black text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">SKU Mapping Admin</h1>
            <p className="text-gray-400">
              {unmappedProducts.length} unmapped products · ${totalRevenue.toFixed(2)} revenue
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-400 mb-2">
              {totalMappings} mapped · ${mappedRevenue.toFixed(2)} revenue
            </div>
            <button
              onClick={handleSave}
              disabled={saving || totalMappings === 0}
              className="bg-[#09fe94] text-black px-6 py-2 rounded font-bold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? "Saving..." : `Save & Reprocess`}
            </button>
          </div>
        </div>

        {saveResult && (
          <div
            className={`mb-4 p-4 rounded ${
              saveResult.startsWith("✓") ? "bg-green-900/30 text-green-300" : "bg-red-900/30 text-red-300"
            }`}
          >
            {saveResult}
          </div>
        )}

        <div className="grid grid-cols-3 gap-6">
          {/* Left: Unmapped Products */}
          <div className="bg-gray-900 rounded-lg p-4">
            <h2 className="text-xl font-bold mb-4">Unmapped Products</h2>
            <div className="space-y-2 max-h-[calc(100vh-250px)] overflow-y-auto">
              {unmappedProducts.map(product => {
                const key = `${product.productName}|||${product.sku}`;
                const mapping = mappings[key];
                const isSelected = selectedProduct?.productName === product.productName;

                return (
                  <div
                    key={key}
                    onClick={() => setSelectedProduct(product)}
                    className={`p-3 rounded cursor-pointer transition-all ${
                      mapping
                        ? "bg-green-900/30 border border-green-500"
                        : isSelected
                        ? "bg-gray-700 border border-[#09fe94]"
                        : "bg-gray-800 hover:bg-gray-700"
                    }`}
                  >
                    <div className="font-bold text-sm">{product.productName}</div>
                    <div className="text-xs text-gray-400 mt-1">
                      {product.sku} · ${product.revenue.toFixed(2)} · {product.transactions} sales
                    </div>
                    {mapping && (
                      <div className="text-xs text-green-400 mt-1">
                        {mapping.action === "match" && `→ ${mapping.matchedSKU}`}
                        {mapping.action === "new" && `→ New product ($${mapping.newCost})`}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Middle: Actions */}
          <div className="bg-gray-900 rounded-lg p-4">
            <h2 className="text-xl font-bold mb-4">
              {selectedProduct ? `Map: ${selectedProduct.productName}` : "Select a Product"}
            </h2>

            {selectedProduct && (
              <div className="space-y-4">
                <div className="bg-gray-800 p-3 rounded">
                  <div className="text-sm text-gray-400">Current SKU</div>
                  <div className="font-bold">{selectedProduct.sku}</div>
                  <div className="text-sm text-gray-400 mt-2">
                    ${selectedProduct.revenue.toFixed(2)} · {selectedProduct.transactions} sales
                  </div>
                </div>

                {selectedProduct.sku !== "NAYAX" && (
                  <div className="bg-gray-800 p-3 rounded">
                    <div className="text-sm text-gray-400 mb-2">Product has SKU but no cost</div>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="Enter cost (e.g., 1.50)"
                      className="w-full bg-gray-700 text-white px-3 py-2 rounded mb-2"
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          const cost = (e.target as HTMLInputElement).value;
                          if (cost) {
                            handleCreateNew(selectedProduct, cost, "");
                          }
                        }
                      }}
                    />
                    <button
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        const cost = input.value;
                        if (cost) {
                          handleCreateNew(selectedProduct, cost, "");
                        }
                      }}
                      className="w-full bg-[#09fe94] text-black px-4 py-2 rounded font-bold"
                    >
                      Update Cost
                    </button>
                  </div>
                )}

                {selectedSuggestions.length > 0 && (
                  <div>
                    <div className="text-sm text-gray-400 mb-2">Suggested Matches</div>
                    <div className="space-y-2">
                      {selectedSuggestions.map((suggestion, idx) => (
                        <div
                          key={`${suggestion.masterSKU}-${idx}`}
                          onClick={() => handleSelectMatch(selectedProduct, suggestion.masterSKU)}
                          className="bg-gray-800 hover:bg-gray-700 p-3 rounded cursor-pointer"
                        >
                          <div className="font-bold text-sm">{suggestion.masterName}</div>
                          <div className="text-xs text-gray-400">
                            {suggestion.masterSKU} · {suggestion.cost}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedProduct.sku === "NAYAX" && (
                  <div className="bg-gray-800 p-3 rounded">
                    <div className="text-sm text-gray-400 mb-2">Create New Product</div>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="Cost (e.g., 1.50)"
                      className="w-full bg-gray-700 text-white px-3 py-2 rounded mb-2"
                      id="newCost"
                    />
                    <input
                      type="text"
                      placeholder="Product Family (optional)"
                      className="w-full bg-gray-700 text-white px-3 py-2 rounded mb-2"
                      id="newFamily"
                    />
                    <button
                      onClick={() => {
                        const cost = (document.getElementById("newCost") as HTMLInputElement).value;
                        const family = (document.getElementById("newFamily") as HTMLInputElement).value;
                        if (cost) {
                          handleCreateNew(selectedProduct, cost, family);
                        }
                      }}
                      className="w-full bg-[#09fe94] text-black px-4 py-2 rounded font-bold"
                    >
                      Create New
                    </button>
                  </div>
                )}

                <button
                  onClick={() => handleSkip(selectedProduct)}
                  className="w-full bg-gray-700 text-white px-4 py-2 rounded"
                >
                  Skip / Clear Mapping
                </button>
              </div>
            )}
          </div>

          {/* Right: SKU Map Search */}
          <div className="bg-gray-900 rounded-lg p-4">
            <h2 className="text-xl font-bold mb-4">Search SKU Map</h2>
            <input
              type="text"
              placeholder="Search products..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-gray-800 text-white px-3 py-2 rounded mb-4"
            />
            <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-y-auto">
              {filteredSKUMap.map((entry, idx) => (
                <div
                  key={`${entry.masterSKU}-${idx}`}
                  onClick={() => {
                    if (selectedProduct) {
                      handleSelectMatch(selectedProduct, entry.masterSKU);
                    }
                  }}
                  className={`p-3 rounded ${
                    selectedProduct ? "bg-gray-800 hover:bg-gray-700 cursor-pointer" : "bg-gray-800"
                  }`}
                >
                  <div className="font-bold text-sm">{entry.masterName}</div>
                  <div className="text-xs text-gray-400">
                    {entry.masterSKU} · {entry.cost}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
