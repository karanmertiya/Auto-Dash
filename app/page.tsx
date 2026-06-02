"use client";

import { useState } from "react";
import Papa from "papaparse";
import { UploadCloud, BarChart2, TrendingUp, AlertCircle } from "lucide-react";
import { cleanData } from "@/lib/data-cleaner";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";

export default function DashboardPage() {
  const [data, setData] = useState<any[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");
  const [rawRowCount, setRawRowCount] = useState(0);

  const onFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setError("");

    const reader = new FileReader();
    reader.onload = (e) => {
      let text = e.target?.result as string;
      
      // Heuristic to handle LinkedIn exports or files with metadata headers:
      // Skip lines until we find one with multiple commas (likely the true CSV header)
      const lines = text.split(/\r?\n/);
      const headerIndex = lines.findIndex(line => (line.match(/,/g) || []).length >= 2);
      if (headerIndex > 0) {
        text = lines.slice(headerIndex).join('\n');
      }

      Papa.parse(text, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: (results) => {
          if (results.errors.length > 0 && results.data.length === 0) {
            setError("Error parsing CSV. Please check the format.");
            return;
          }

          const parsedData = results.data as Record<string, unknown>[];
          if (parsedData.length === 0) {
            setError("CSV is empty.");
            return;
          }

          const cleanedData = cleanData(parsedData);
          if (cleanedData.length === 0) {
            setError("No usable rows remained after cleaning.");
            return;
          }

          const headers = Object.keys(cleanedData[0] as object);
          setRawRowCount(parsedData.length);
          setColumns(headers);
          setData(cleanedData);
        },
        error: (err: any) => {
          setError(err.message);
        },
      });
    };
    reader.readAsText(file);
  };

  // Find a category column (string) and a metric column (number)
  const getChartData = () => {
    if (data.length === 0) return { categoryKey: "", metricKey: "", chartData: [] };

    let categoryKey = "";
    let metricKey = "";

    // Naive heuristic: find first string column and first number column
    for (const col of columns) {
      if (!categoryKey && typeof data[0][col] === "string") {
        categoryKey = col;
      }
      if (!metricKey && typeof data[0][col] === "number") {
        metricKey = col;
      }
    }

    // Fallback if no string column
    if (!categoryKey) categoryKey = columns[0];
    if (!metricKey) metricKey = columns[1] || columns[0];

    // Aggregate data for the bar chart
    const aggregated: Record<string, number> = {};
    data.forEach((row) => {
      const cat = row[categoryKey];
      const val = row[metricKey];
      if (cat !== undefined && val !== undefined) {
        const catStr = String(cat);
        aggregated[catStr] = (aggregated[catStr] || 0) + Number(val);
      }
    });

    const chartData = Object.keys(aggregated).map((key) => ({
      [categoryKey]: key,
      [metricKey]: aggregated[key],
    })).slice(0, 20); // Limit to top 20 for readability

    return { categoryKey, metricKey, chartData };
  };

  const { categoryKey, metricKey, chartData } = getChartData();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Auto-Dash Simple</h1>
            <p className="text-slate-500 mt-1">Instant, client-side CSV dashboarding.</p>
          </div>
        </header>

        {!data.length ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-sm transition-colors hover:border-blue-400">
            <label className="flex cursor-pointer flex-col items-center justify-center">
              <div className="rounded-full bg-blue-50 p-4 text-blue-600 mb-4">
                <UploadCloud className="h-8 w-8" />
              </div>
              <span className="text-lg font-semibold">Upload a CSV dataset</span>
              <span className="mt-2 text-sm text-slate-500">
                All processing happens in your browser. No data is sent to a server.
              </span>
              <input
                type="file"
                className="sr-only"
                accept=".csv"
                onChange={onFileUpload}
              />
            </label>
            {error && (
              <div className="mt-6 flex items-center justify-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
                <AlertCircle className="h-5 w-5" />
                <span className="text-sm font-medium">{error}</span>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between rounded-xl bg-white p-4 shadow-sm border border-slate-200">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-green-100 p-2 text-green-700">
                  <TrendingUp className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-sm font-bold">{fileName}</h2>
                  <p className="text-xs text-slate-500">
                    {data.length} clean rows loaded
                    {rawRowCount > data.length ? ` from ${rawRowCount} parsed rows` : ""}
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  setData([]);
                  setRawRowCount(0);
                }}
                className="rounded-md bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-200"
              >
                Upload New File
              </button>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
                <div className="mb-4 flex items-center gap-2 border-b border-slate-100 pb-4">
                  <BarChart2 className="h-5 w-5 text-blue-600" />
                  <h3 className="font-bold">
                    Total {metricKey} by {categoryKey}
                  </h3>
                </div>
                <div className="h-[300px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey={categoryKey} tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip
                        contentStyle={{ borderRadius: "8px", border: "none", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                      />
                      <Legend />
                      <Bar dataKey={metricKey} fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
                <div className="mb-4 flex items-center gap-2 border-b border-slate-100 pb-4">
                  <TrendingUp className="h-5 w-5 text-indigo-600" />
                  <h3 className="font-bold">
                    Trend of {metricKey}
                  </h3>
                </div>
                <div className="h-[300px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey={categoryKey} tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip
                        contentStyle={{ borderRadius: "8px", border: "none", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                      />
                      <Legend />
                      <Line type="monotone" dataKey={metricKey} stroke="#4f46e5" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
