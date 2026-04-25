"use client";

import { useState } from "react";
import { Download, WandSparkles } from "lucide-react";

import { DatasetSelector } from "@/components/dataset-selector";
import { JsonInspector } from "@/components/json-inspector";
import { Dataset, apiPost, artifactUrl } from "@/lib/api";

export default function SemanticPage() {
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [goal, setGoal] = useState("Create a governed semantic model with reusable measures and time intelligence.");
  const [model, setModel] = useState<any>(null);

  async function generate() {
    if (!dataset) return;
    const next = await apiPost<any>(`/api/semantic-models/datasets/${dataset.id}`, { goal, actor: "local-user" });
    setModel(next);
    window.localStorage.setItem("dashforge.semanticModelId", next.id);
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Semantic model</h1>
          <p className="text-sm text-zinc-600">Fields, entities, measures, ownership, and metric expressions stay exportable.</p>
        </div>
        <DatasetSelector onSelect={setDataset} />
      </div>
      <div className="rounded border border-line bg-white p-4">
        <label className="text-sm font-medium">Modeling goal</label>
        <textarea className="focus-ring mt-2 w-full rounded border-line text-sm" value={goal} onChange={(event) => setGoal(event.target.value)} rows={3} />
        <div className="mt-3 flex flex-wrap gap-2">
          <button className="focus-ring inline-flex items-center gap-2 rounded bg-cyan-700 px-3 py-2 text-sm text-white" onClick={generate}>
            <WandSparkles className="h-4 w-4" />
            Generate draft model
          </button>
          {model ? (
            <>
              <a className="focus-ring inline-flex items-center gap-2 rounded border border-zinc-300 bg-white px-3 py-2 text-sm" href={artifactUrl(`/api/artifacts/semantic-models/${model.id}.yaml`)}>
                <Download className="h-4 w-4" />
                YAML
              </a>
              <a className="focus-ring inline-flex items-center gap-2 rounded border border-zinc-300 bg-white px-3 py-2 text-sm" href={artifactUrl(`/api/artifacts/semantic-models/${model.id}.json`)}>
                <Download className="h-4 w-4" />
                JSON
              </a>
            </>
          ) : null}
        </div>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <section className="rounded border border-line bg-white">
          <header className="border-b border-line px-4 py-3 text-sm font-semibold">YAML</header>
          <pre className="max-h-[620px] overflow-auto p-4 text-xs leading-5">{model?.model_yaml ?? "No model generated yet."}</pre>
        </section>
        <JsonInspector title="Semantic model JSON" value={model?.model_json ?? null} />
      </div>
    </div>
  );
}

