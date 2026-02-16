"use client";

import Link from "next/link";
import TransactionUpload from "@/components/TransactionUpload";

export default function UploadPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="border-b border-[#222] bg-black">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-[#09fe94]">Admin - Upload Data</h1>
              <p className="text-gray-400 text-sm mt-1">
                Client-side upload - No timeout limits!
              </p>
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
        {/* Upload Component */}
        <TransactionUpload />

        {/* Instructions */}
        <div className="mt-8 bg-[#111] border border-[#222] rounded-2xl p-6">
          <h3 className="text-lg font-semibold mb-4">📋 How It Works</h3>
          <ul className="space-y-3 text-gray-300">
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">✓</span>
              <span>
                <strong>Client-Side Processing:</strong> Your file is processed in your browser, not on the server. This eliminates timeout issues entirely.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">✓</span>
              <span>
                <strong>Automatic Deduplication:</strong> The system creates unique keys based on timestamp, machine, product, and total. Re-uploading the same data won't create duplicates.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">✓</span>
              <span>
                <strong>Incremental Uploads:</strong> Upload any timeframe (1 day, 1 week, YTD) - the system adds only new transactions.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">✓</span>
              <span>
                <strong>Location Extraction:</strong> If the Location column is empty, the system extracts it from the Machine column automatically.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#09fe94] font-bold">✓</span>
              <span>
                <strong>Fast Batch Processing:</strong> Data is uploaded in batches of 100 rows for optimal speed and reliability.
              </span>
            </li>
          </ul>

          <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <p className="text-blue-300 text-sm">
              <strong>💡 Pro Tip:</strong> After upload completes, refresh the dashboard page to see your updated data reflected in the charts and totals.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
