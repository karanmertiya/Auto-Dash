"use client";

import { useState } from "react";
import { Play, WandSparkles } from "lucide-react";

import { CodePanel } from "@/components/code-panel";
import { DatasetSelector } from "@/components/dataset-selector";
import { JsonInspector } from "@/components/json-inspector";
import { StatusPill } from "@/components/status-pill";
import { Dataset, apiPost } from "@/lib/api";

export default function CleaningPage() {
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [plan, setPlan] = useState<any>(null);
  const [script, setScript] = useState("");
  const [execution, setExecution] = useState<any>(null);
  const [busy, setBusy] = useState("");

  async function generate() {
    if (!dataset) return;
    setBusy("Generating plan");
    const next = await apiPost<any>(`/api/cleaning/datasets/${dataset.id}/plan`);
    setPlan(next);
    setScript(next.script);
    window.localStorage.setItem("dashforge.cleaningPlanId", next.id);
    setBusy("");
  }

  async function execute() {
    if (!plan) return;
    setBusy("Executing script");
    const result = await apiPost<any>(`/api/cleaning/plans/${plan.id}/execute`, { script, actor: "local-user" });
    setExecution(result);
    setBusy("");
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Cleaning plan review</h1>
          <p className="text-sm text-zinc-600">Generated transformations are editable and must be run explicitly.</p>
        </div>
        <DatasetSelector onSelect={setDataset} />
      </div>
      <div className="flex flex-wrap gap-2">
        <button className="focus-ring inline-flex items-center gap-2 rounded bg-cyan-700 px-3 py-2 text-sm text-white" onClick={generate}>
          <WandSparkles className="h-4 w-4" />
          Generate plan
        </button>
        <button className="focus-ring inline-flex items-center gap-2 rounded bg-zinc-900 px-3 py-2 text-sm text-white disabled:opacity-50" disabled={!plan} onClick={execute}>
          <Play className="h-4 w-4" />
          Execute reviewed script
        </button>
        {busy ? <span className="rounded border border-line bg-white px-3 py-2 text-sm text-zinc-600">{busy}</span> : null}
        {execution ? <StatusPill status={execution.status} /> : null}
      </div>
      <div className="grid gap-5 lg:grid-cols-[1fr_420px]">
        <CodePanel title="Editable Polars transform(df) script" value={script} onChange={setScript} />
        <div className="space-y-5">
          <JsonInspector title="Cleaning plan JSON" value={plan} />
          <JsonInspector title="Execution result" value={execution} />
        </div>
      </div>
    </div>
  );
}

