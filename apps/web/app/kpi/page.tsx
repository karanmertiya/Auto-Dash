"use client";

import { useEffect, useState } from "react";
import { WandSparkles } from "lucide-react";

import { DatasetSelector } from "@/components/dataset-selector";
import { JsonInspector } from "@/components/json-inspector";
import { MetricPlan } from "@/components/metric-plan";
import { Dataset, apiGet, apiPost } from "@/lib/api";

export default function KpiPage() {
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [models, setModels] = useState<any[]>([]);
  const [semanticModelId, setSemanticModelId] = useState("");
  const [goal, setGoal] = useState("Monitor revenue, order volume, customer segments, and operational exceptions.");
  const [plan, setPlan] = useState<any>(null);

  useEffect(() => {
    if (!dataset) return;
    apiGet<any[]>(`/api/semantic-models/datasets/${dataset.id}`).then((items) => {
      setModels(items);
      const current = window.localStorage.getItem("dashforge.semanticModelId");
      setSemanticModelId(items.find((item) => item.id === current)?.id ?? items[0]?.id ?? "");
    });
  }, [dataset]);

  async function generate() {
    if (!semanticModelId) return;
    const next = await apiPost<any>(`/api/recommendations/semantic-models/${semanticModelId}/dashboard-plan`, { goal, actor: "local-user" });
    setPlan(next);
    window.localStorage.setItem("dashforge.dashboardPlanId", next.id);
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">KPI and chart plan</h1>
          <p className="text-sm text-zinc-600">Recommendations reference governed metric expressions and warn on ambiguity.</p>
        </div>
        <DatasetSelector onSelect={setDataset} />
      </div>
      <section className="rounded border border-line bg-white p-4">
        <div className="grid gap-3 md:grid-cols-[260px_1fr]">
          <label className="text-sm">
            <span className="font-medium">Semantic model</span>
            <select className="focus-ring mt-2 w-full rounded border-line text-sm" value={semanticModelId} onChange={(event) => setSemanticModelId(event.target.value)}>
              {models.map((model) => <option key={model.id} value={model.id}>v{model.version_number} {model.id.slice(0, 8)}</option>)}
            </select>
          </label>
          <label className="text-sm">
            <span className="font-medium">Dashboard goal</span>
            <textarea className="focus-ring mt-2 w-full rounded border-line text-sm" rows={3} value={goal} onChange={(event) => setGoal(event.target.value)} />
          </label>
        </div>
        <button className="focus-ring mt-3 inline-flex items-center gap-2 rounded bg-cyan-700 px-3 py-2 text-sm text-white" onClick={generate}>
          <WandSparkles className="h-4 w-4" />
          Generate plan
        </button>
      </section>
      <MetricPlan plan={plan?.plan_json} />
      <JsonInspector title="Dashboard plan JSON" value={plan} />
    </div>
  );
}

