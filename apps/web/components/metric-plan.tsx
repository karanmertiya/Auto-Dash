import { AlertTriangle } from "lucide-react";

export function MetricPlan({ plan }: { plan: any }) {
  if (!plan) return null;
  return (
    <div className="space-y-4">
      {plan.warnings?.length ? (
        <div className="flex gap-2 rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{plan.warnings.join(" ")}</span>
        </div>
      ) : null}
      <div className="grid gap-3 md:grid-cols-3">
        {plan.kpis?.map((kpi: any) => (
          <article key={kpi.name} className="rounded border border-line bg-white p-4">
            <p className="text-xs uppercase text-zinc-500">{kpi.name}</p>
            <p className="mt-2 text-sm font-medium text-zinc-950">{kpi.business_question}</p>
            <code className="mt-3 block rounded bg-zinc-100 p-2 text-xs text-zinc-800">{kpi.metric_expression}</code>
          </article>
        ))}
      </div>
      <div className="rounded border border-line bg-white">
        <div className="border-b border-line px-4 py-3 text-sm font-semibold">Recommended charts</div>
        <div className="divide-y divide-line">
          {plan.charts?.map((chart: any) => (
            <div key={chart.title} className="grid gap-2 px-4 py-3 text-sm md:grid-cols-[1fr_160px_1fr]">
              <span className="font-medium">{chart.title}</span>
              <span className="text-zinc-600">{chart.chart_type}</span>
              <span className="text-zinc-600">{chart.rationale}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

