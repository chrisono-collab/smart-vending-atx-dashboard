"use client";

import { useState } from "react";
import { Upload, CheckCircle, XCircle, Loader2 } from "lucide-react";
import Link from "next/link";

interface UploadResult {
  success: boolean;
  filename?: string;
  totalTransactions?: number;
  duplicatesRemoved?: number;
  mappingCoverage?: number;
  unmappedRevenue?: number;
  totalRevenue?: number;
  totalProfit?: number;
  error?: string;
}

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.name.endsWith('.xlsx') || droppedFile.name.endsWith('.xls'))) {
      setFile(droppedFile);
      setResult(null);
    } else {
      alert('Please upload an Excel file (.xlsx or .xls)');
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        setResult({
          success: true,
          ...data
        });
        setFile(null);
      } else {
        setResult({
          success: false,
          error: data.error || 'Upload failed'
        });
      }
    } catch (error: any) {
      setResult({
        success: false,
        error: error.message || 'Upload failed'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="border-b border-[#222] bg-black">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-[#09fe94]">Admin - Upload Data</h1>
              <p className="text-gray-400 text-sm mt-1">Upload transaction log files to Supabase</p>
            </div>
            <Link
              href="/"
              className="px-4 py-2 bg-[#09fe94]/10 text-[#09fe94] rounded-lg hover:bg-[#09fe94]/20 transition-colors border border-[#09fe94]/30"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Upload Area */}
        <div
          className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all ${
            isDragging
              ? 'border-[#09fe94] bg-[#09fe94]/5'
              : 'border-[#333] hover:border-[#555]'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-xl font-semibold mb-2">
            {file ? file.name : 'Drag & drop your transaction log'}
          </h2>
          <p className="text-gray-400 mb-6">
            {file ? 'Ready to upload' : 'or click to browse for Excel files (.xlsx, .xls)'}
          </p>

          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileSelect}
            className="hidden"
            id="fileInput"
          />

          <div className="flex gap-4 justify-center">
            <label
              htmlFor="fileInput"
              className="px-6 py-3 bg-[#111] border border-[#333] text-white rounded-lg hover:bg-[#1a1a1a] transition-colors cursor-pointer"
            >
              Browse Files
            </label>

            {file && (
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="px-6 py-3 bg-[#09fe94] text-black font-semibold rounded-lg hover:bg-[#07cc75] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Upload & Process'
                )}
              </button>
            )}
          </div>
        </div>

        {/* Result Display */}
        {result && (
          <div className={`mt-8 rounded-2xl p-6 ${
            result.success
              ? 'bg-green-500/10 border-2 border-green-500/30'
              : 'bg-red-500/10 border-2 border-red-500/30'
          }`}>
            <div className="flex items-center gap-3 mb-4">
              {result.success ? (
                <CheckCircle className="w-8 h-8 text-green-400" />
              ) : (
                <XCircle className="w-8 h-8 text-red-400" />
              )}
              <h3 className="text-xl font-semibold">
                {result.success ? 'Upload Successful!' : 'Upload Failed'}
              </h3>
            </div>

            {result.success ? (
              <div className="grid grid-cols-2 gap-4 mt-6">
                <div className="bg-black/30 rounded-lg p-4">
                  <p className="text-gray-400 text-sm mb-1">Total Transactions</p>
                  <p className="text-2xl font-bold text-[#09fe94]">{result.totalTransactions?.toLocaleString()}</p>
                </div>
                <div className="bg-black/30 rounded-lg p-4">
                  <p className="text-gray-400 text-sm mb-1">Duplicates Removed</p>
                  <p className="text-2xl font-bold text-yellow-400">{result.duplicatesRemoved?.toLocaleString()}</p>
                </div>
                <div className="bg-black/30 rounded-lg p-4">
                  <p className="text-gray-400 text-sm mb-1">Mapping Coverage</p>
                  <p className="text-2xl font-bold text-blue-400">{result.mappingCoverage?.toFixed(1)}%</p>
                </div>
                <div className="bg-black/30 rounded-lg p-4">
                  <p className="text-gray-400 text-sm mb-1">Unmapped Revenue</p>
                  <p className="text-2xl font-bold text-red-400">${result.unmappedRevenue?.toFixed(2)}</p>
                </div>
                <div className="bg-black/30 rounded-lg p-4">
                  <p className="text-gray-400 text-sm mb-1">Total Revenue</p>
                  <p className="text-2xl font-bold text-white">${result.totalRevenue?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
                </div>
                <div className="bg-black/30 rounded-lg p-4">
                  <p className="text-gray-400 text-sm mb-1">Total Profit</p>
                  <p className="text-2xl font-bold text-[#09fe94]">${result.totalProfit?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
                </div>
              </div>
            ) : (
              <p className="text-red-300">{result.error}</p>
            )}
          </div>
        )}

        {/* Instructions */}
        <div className="mt-8 bg-[#111] border border-[#222] rounded-2xl p-6">
          <h3 className="text-lg font-semibold mb-4">📋 Instructions</h3>
          <ul className="space-y-2 text-gray-300">
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">1.</span>
              <span>Export your transaction log from VendSoft/USAT as an Excel file</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">2.</span>
              <span>Drag & drop the file above or click "Browse Files" to select it</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">3.</span>
              <span>Click "Upload & Process" to import transactions into Supabase</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">4.</span>
              <span>The system will automatically deduplicate and map products</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">5.</span>
              <span>Return to the dashboard to see your updated data</span>
            </li>
          </ul>
        </div>
      </main>
    </div>
  );
}
