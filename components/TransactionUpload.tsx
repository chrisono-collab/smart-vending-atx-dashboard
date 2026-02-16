'use client';

import React, { useState } from 'react';
import * as XLSX from 'xlsx';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export default function TransactionUpload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const supabase = createClient(supabaseUrl, supabaseAnonKey);

  const cleanLocation = (location: string, machine: string) => {
    if (!location || location.trim() === '') {
      const match = machine.match(/\[.*?\]\s*(.+)/);
      return match ? match[1].trim() : machine;
    }
    return location.trim();
  };

  const createDedupKey = (timestamp: Date, machine: string, product: string, total: number) => {
    const tsStr = timestamp.toISOString().substring(0, 19); // YYYY-MM-DDTHH:MM:SS
    const machineMatch = machine.match(/\[(\d+)\]/);
    const machineId = machineMatch ? machineMatch[1] : machine.replace(/[^a-z0-9]/gi, '').toLowerCase();
    const productId = product.replace(/[^a-z0-9]/gi, '').toLowerCase();
    return `${tsStr}_${machineId}_${productId}_${total.toFixed(2)}`;
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);
    setStatus('Reading file...');

    const reader = new FileReader();
    reader.onload = async (evt) => {
      try {
        const bstr = evt.target?.result;
        const wb = XLSX.read(bstr, { type: 'binary' });
        const wsname = wb.SheetNames[0];
        const ws = wb.Sheets[wsname];

        // Convert to JSON, starting from row 4 (skip first 3 header rows)
        const rawData: any[] = XLSX.utils.sheet_to_json(ws, { header: 1, range: 3 });

        setStatus(`Processing ${rawData.length} transactions...`);

        // Map data to database schema
        const transactions = rawData
          .filter(row => row[0] && row[7]) // Filter out empty rows
          .map((row) => {
            // Parse Excel date serial number to JavaScript Date
            let timestamp: Date;
            if (typeof row[0] === 'number') {
              // Excel serial date
              timestamp = new Date((row[0] - 25569) * 86400 * 1000);
            } else {
              timestamp = new Date(row[0]);
            }

            const location = row[1] || '';
            const machine = row[2] || '';
            const product = row[3] || 'Unknown';
            const revenue = parseFloat(row[7]) || 0;
            const quantity = parseInt(row[6]) || 1;

            return {
              timestamp: timestamp.toISOString(),
              date: timestamp.toISOString().split('T')[0], // YYYY-MM-DD
              location: cleanLocation(location, machine),
              master_sku: 'UNMAPPED',
              master_name: String(product),
              product_family: null,
              type: 'Unknown',
              revenue: revenue,
              cost: 0,
              quantity: quantity,
              profit: revenue,
              gross_margin_percent: 100,
              mapping_tier: 'unmapped',
              dedup_key: createDedupKey(timestamp, machine, product, revenue)
            };
          });

        setStatus(`Uploading ${transactions.length} transactions in batches...`);

        // Batch processing (100 rows at a time)
        const batchSize = 100;
        let inserted = 0;

        for (let i = 0; i < transactions.length; i += batchSize) {
          const batch = transactions.slice(i, i + batchSize);

          const { error } = await supabase
            .from('transactions')
            .upsert(batch, { onConflict: 'dedup_key', ignoreDuplicates: true });

          if (error) {
            console.error('Batch error:', error);
            throw error;
          }

          inserted += batch.length;
          const currentProgress = Math.round((inserted / transactions.length) * 100);
          setProgress(currentProgress);
          setStatus(`Uploaded ${inserted} of ${transactions.length} transactions...`);
        }

        setStatus(`✓ Upload Complete! ${transactions.length} transactions processed. Refresh to see updated data.`);
        setProgress(100);
      } catch (err: any) {
        console.error('Upload error:', err);
        setStatus(`Error: ${err.message}`);
      } finally {
        setUploading(false);
      }
    };
    reader.readAsBinaryString(file);
  };

  return (
    <div className="p-6 border border-gray-700 rounded-lg bg-gray-800 shadow-lg">
      <h3 className="text-lg font-bold mb-4 text-white">Upload Transaction Log</h3>
      <input
        type="file"
        accept=".xlsx,.xls"
        onChange={handleFileUpload}
        disabled={uploading}
        className="block w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
      />
      {uploading && (
        <div className="mt-4">
          <div className="w-full bg-gray-700 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm mt-2 text-gray-300">{status}</p>
        </div>
      )}
      {!uploading && status && (
        <p className="text-sm mt-2 text-green-400">{status}</p>
      )}
    </div>
  );
}
