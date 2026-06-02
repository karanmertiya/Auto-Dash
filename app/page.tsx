"use client";

import { useState } from "react";
import Papa from "papaparse";
import { UploadCloud, BarChart2, TrendingUp, AlertCircle, Bot, FileText, Loader2 } from "lucide-react";
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
  
  // AI Report State
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [aiReport, setAiReport] = useState<string | null>(null);

  const onFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const names = Array.from(files).map(f => f.name).join(", ");
    setFileName(names.length > 50 ? `${files.length} files selected` : names);
    setError("");
    setAiReport(null);

    try {
      const allParsedData: any[] = [];
      let totalRaw = 0;

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileData = await new Promise<any[]>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (e) => {
            let text = e.target?.result as string;
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
                  console.warn(`Skipping ${file.name} due to parsing errors.`);
                  resolve([]);
                  return;
                }
                const parsed = results.data as Record<string, unknown>[];
                // Filter out completely empty rows
                const validRows = parsed.filter(row => Object.values(row).some(val => val !== null && val !== ''));
                resolve(validRows.map(row => ({ ...row, Source_File: file.name })));
              },
              error: (err: any) => {
                console.warn(`Skipping ${file.name} due to error:`, err);
                resolve([]);
              }
            });
          };
          reader.readAsText(file);
        });
        totalRaw += fileData.length;
        allParsedData.push(...fileData);
      }

      if (allParsedData.length === 0) {
        setError("CSV files are empty.");
        return;
      }

      const cleanedData = cleanData(allParsedData);
      if (cleanedData.length === 0) {
        setError("No usable rows remained after cleaning.");
        return;
      }

      const headers = Object.keys(cleanedData[0] as object);
      setRawRowCount(totalRaw);
      setColumns(headers);
      setData(cleanedData);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const getChartData = () => {
    if (data.length === 0) return { categoryKey: "", metricKey: "", chartData: [] };

    let categoryKey = "";
    let metricKey = "";
    let hasNumericMetric = false;

    for (const col of columns) {
      if (!categoryKey && typeof data[0][col] === "string") {
        categoryKey = col;
      }
      if (!metricKey && typeof data[0][col] === "number") {
        metricKey = col;
        hasNumericMetric = true;
      }
    }

    if (!categoryKey) categoryKey = columns[0];

    const aggregated: Record<string, number> = {};

    if (hasNumericMetric) {
      data.forEach((row) => {
        const cat = row[categoryKey];
        const val = row[metricKey];
        if (cat !== undefined && val !== undefined) {
          const catStr = String(cat);
          aggregated[catStr] = (aggregated[catStr] || 0) + Number(val);
        }
      });
    } else {
      metricKey = "Count";
      data.forEach((row) => {
        const cat = row[categoryKey];
        if (cat !== undefined) {
          const catStr = String(cat);
          aggregated[catStr] = (aggregated[catStr] || 0) + 1;
        }
      });
    }

    const chartData = Object.keys(aggregated)
      .map((key) => ({
        [categoryKey]: key,
        [metricKey]: aggregated[key],
      }))
      .sort((a, b) => (b[metricKey] as number) - (a[metricKey] as number))
      .slice(0, 20);

    return { categoryKey, metricKey, chartData };
  };

  const generateAIReport = async () => {
    setIsGeneratingReport(true);
    setError("");
    
    try {
      const datasetId = "dataset_" + Date.now();
      
      const apiUrl = "https://auto-agent-api-386032878543.us-central1.run.app";
      const uploadRes = await fetch(`${apiUrl}/api/data-agent/upload-dataset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          datasetId: datasetId,
          data: data
        })
      });
      
      if (!uploadRes.ok) throw new Error("Failed to upload dataset to Agent Backend.");

      // Step 2: Trigger recursive analysis (Job Recommendation mode as default for this demo)
      const query = "Analyze this dataset and generate a comprehensive Job Recommendation report. Identify the top companies and positions the users are associated with, and recommend targeted job search strategies.";
      
      const analyzeRes = await fetch(`${apiUrl}/api/data-agent/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          datasetId: datasetId,
          query: query
        })
      });

      const analysisData = await analyzeRes.json();
      
      if (!analyzeRes.ok) throw new Error(analysisData.error || "Failed to generate report.");
      
      setAiReport(analysisData.report);
      
    } catch (err: any) {
      setError("AI Engine Error: " + err.message);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const { categoryKey, metricKey, chartData } = getChartData();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Auto-Dash Agentic</h1>
            <p className="text-slate-500 mt-1">Client-side processing + Recursive AI Engine.</p>
          </div>
        </header>

        {!data.length ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-sm transition-colors hover:border-blue-400">
            <label className="flex cursor-pointer flex-col items-center justify-center">
              <div className="rounded-full bg-blue-50 p-4 text-blue-600 mb-4">
                <UploadCloud className="h-8 w-8" />
              </div>
              <span className="text-lg font-semibold">Upload CSV datasets</span>
              <span className="mt-2 text-sm text-slate-500">
                You can select multiple files. Data will be combined & masked.
              </span>
              <input
                type="file"
                className="sr-only"
                accept=".csv"
                multiple
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
              <div className="flex gap-4">
                <button
                  onClick={generateAIReport}
                  disabled={isGeneratingReport}
                  className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
                >
                  {isGeneratingReport ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Analyzing Recursively...
                    </>
                  ) : (
                    <>
                      <Bot className="h-4 w-4" />
                      Generate AI Report
                    </>
                  )}
                </button>
                <button
                  onClick={() => {
                    setData([]);
                    setRawRowCount(0);
                    setAiReport(null);
                  }}
                  className="rounded-md bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-200"
                >
                  Upload New File
                </button>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
                <AlertCircle className="h-5 w-5" />
                <span className="text-sm font-medium">{error}</span>
              </div>
            )}

            {aiReport && (
              <div className="rounded-xl bg-indigo-50 p-6 shadow-sm border border-indigo-100 mb-6">
                <div className="mb-4 flex items-center gap-2 border-b border-indigo-100 pb-4">
                  <FileText className="h-6 w-6 text-indigo-700" />
                  <h3 className="font-bold text-lg text-indigo-900">Agentic Analysis Report</h3>
                </div>
                <div className="prose prose-indigo max-w-none text-slate-800 whitespace-pre-wrap">
                  {aiReport}
                </div>
              </div>
            )}

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
