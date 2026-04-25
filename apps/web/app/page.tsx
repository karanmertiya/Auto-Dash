"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, RefreshCw, UploadCloud } from "lucide-react";

import { Dataset, apiGet, uploadDataset } from "@/lib/api";
import { StatusPill } from "@/components/status-pill";

export default function UploadPage() {
  const router = useRouter();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    const items = await apiGet<Dataset[]>("/api/datasets");
    setDatasets(items);
  }

  useEffect(() => {
    refresh().catch(() => setDatasets([]));
  }, []);

  async function onUpload(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const dataset = await uploadDataset(file);
      window.localStorage.setItem("dashforge.datasetId", dataset.id);
      await refresh();
      router.push(`/datasets/${dataset.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-5 lg:grid-cols-[420px_1fr]">
        <div className="rounded border border-line bg-white p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="rounded bg-cyan-700 p-2 text-white">
              <UploadCloud className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">Ingest dataset</h1>
              <p className="text-sm text-zinc-600">CSV, Excel, JSON, Parquet, or SQL snapshot through the API.</p>
            </div>
          </div>
          <label className="flex h-48 cursor-pointer flex-col items-center justify-center rounded border border-dashed border-zinc-300 bg-panel text-center hover:border-cyan-600">
            <UploadCloud className="mb-3 h-8 w-8 text-cyan-700" />
            <span className="text-sm font-medium">Choose a local file</span>
            <span className="mt-1 text-xs text-zinc-500">Raw upload is preserved unchanged</span>
            <input
              type="file"
              className="sr-only"
              accept=".csv,.xlsx,.xls,.json,.ndjson,.parquet"
              disabled={busy}
              onChange={(event) => onUpload(event.target.files?.[0])}
            />
          </label>
          {busy ? <p className="mt-3 text-sm text-cyan-800">Profiling upload...</p> : null}
          {error ? <p className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</p> : null}
        </div>

        <div className="rounded border border-line bg-white">
          <header className="flex items-center justify-between border-b border-line px-4 py-3">
            <h2 className="text-sm font-semibold">Datasets</h2>
            <button className="focus-ring rounded border border-zinc-300 p-1.5 text-zinc-700 hover:bg-zinc-50" title="Refresh" onClick={() => refresh()}>
              <RefreshCw className="h-4 w-4" />
            </button>
          </header>
          <div className="divide-y divide-line">
            {datasets.map((dataset) => (
              <Link
                key={dataset.id}
                href={`/datasets/${dataset.id}`}
                className="grid gap-3 px-4 py-3 hover:bg-zinc-50 md:grid-cols-[1fr_120px_120px_32px]"
                onClick={() => window.localStorage.setItem("dashforge.datasetId", dataset.id)}
              >
                <div>
                  <p className="font-medium text-zinc-950">{dataset.name}</p>
                  <p className="text-xs text-zinc-500">{dataset.id}</p>
                </div>
                <span className="text-sm text-zinc-600">{dataset.source_type}</span>
                <StatusPill status={dataset.status} />
                <ArrowRight className="h-4 w-4 text-zinc-400" />
              </Link>
            ))}
            {datasets.length === 0 ? <p className="px-4 py-8 text-sm text-zinc-500">No datasets ingested yet.</p> : null}
          </div>
        </div>
      </section>
    </div>
  );
}

