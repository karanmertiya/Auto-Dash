from __future__ import annotations

import json
import re

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import not_found
from app.db.models import DashboardArtifact, DashboardPlan, DatasetVersion, SemanticModel
from app.modules.collaboration.audit import AuditService
from app.modules.dashboard.schemas import DashboardArtifactDocument
from app.modules.ingestion.service import read_dataframe


class DashboardGenerationService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.audit = AuditService(session)

    def generate_nextjs_artifact(
        self,
        *,
        dashboard_plan_id: str,
        actor: str = "local-user",
    ) -> DashboardArtifact:
        plan = self.session.get(DashboardPlan, dashboard_plan_id)
        if plan is None:
            raise not_found("DashboardPlan", dashboard_plan_id)
        semantic = self.session.get(SemanticModel, plan.semantic_model_id)
        if semantic is None:
            raise not_found("SemanticModel", plan.semantic_model_id)
        version = self.session.get(DatasetVersion, semantic.dataset_version_id)
        if version is None:
            raise not_found("DatasetVersion", semantic.dataset_version_id)
        rows = self._preview_rows(version)
        files = {
            "app/dashforge-generated/page.tsx": self._page_code(plan.plan_json, semantic.model_json, rows),
            "README.md": self._artifact_readme(plan.plan_json),
        }
        document = DashboardArtifactDocument(
            dashboard_plan_id=plan.id,
            files=files,
            instructions=[
                "Copy files into a Next.js app with recharts installed.",
                "Replace embedded preview rows with a governed API route for production refresh.",
            ],
        )
        artifact_dir = self.settings.storage_dir / "artifacts" / plan.id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        for relative_path, content in files.items():
            target = artifact_dir / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        manifest_path = artifact_dir / "manifest.json"
        manifest_path.write_text(document.model_dump_json(indent=2), encoding="utf-8")
        record = DashboardArtifact(
            dashboard_plan_id=plan.id,
            artifact_type="nextjs",
            path=str(artifact_dir),
            metadata_json=document.model_dump(mode="json"),
        )
        self.session.add(record)
        self.audit.log(
            action="dashboard_artifact.generated",
            entity_type="dashboard_artifact",
            entity_id=record.id,
            actor=actor,
            payload={"dashboard_plan_id": plan.id, "framework": "nextjs"},
        )
        self.session.commit()
        self.session.refresh(record)
        return record

    def _preview_rows(self, version: DatasetVersion) -> list[dict]:
        path = version.cleaned_path or version.staged_path
        return read_dataframe(path).head(500).to_dicts()

    def _page_code(self, plan: dict, semantic: dict, rows: list[dict]) -> str:
        plan_json = json.dumps(plan, indent=2, default=str)
        semantic_json = json.dumps(semantic, indent=2, default=str)
        rows_json = json.dumps(rows, indent=2, default=str)
        return f'''"use client";

import {{
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
}} from "recharts";

const dashboardPlan = {plan_json};
const semanticModel = {semantic_json};
const rows = {rows_json};

function numericValue(value: unknown): number {{
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}}

function computeMetric(expression: string): number {{
  const match = expression.match(/^(sum|avg)\\((.+)\\)$/);
  if (!match) return 0;
  const [, aggregation, column] = match;
  const values = rows.map((row) => numericValue(row[column]));
  const total = values.reduce((acc, value) => acc + value, 0);
  return aggregation === "avg" ? total / Math.max(values.length, 1) : total;
}}

function metricExpression(metricName: string): string {{
  return semanticModel.metrics.find((metric: any) => metric.name === metricName)?.expression ?? "";
}}

function groupedRows(dimension: string | null, metricExpressionText: string) {{
  if (!dimension) return [];
  const metricColumn = metricExpressionText.match(/\\((.+)\\)/)?.[1] ?? "";
  const grouped = new Map<string, number>();
  for (const row of rows) {{
    const key = String(row[dimension] ?? "Unknown");
    grouped.set(key, (grouped.get(key) ?? 0) + numericValue(row[metricColumn]));
  }}
  return Array.from(grouped.entries()).map(([name, value]) => ({{ name, value }})).slice(0, 12);
}}

export default function DashForgeGeneratedDashboard() {{
  return (
    <main className="min-h-screen bg-slate-950 p-8 text-slate-100">
      <section className="mx-auto max-w-7xl space-y-6">
        <div className="flex items-start justify-between gap-6">
          <div>
            <p className="text-sm uppercase tracking-wide text-cyan-300">DashForge Generated Dashboard</p>
            <h1 className="mt-2 text-3xl font-semibold">{self._tsx_text(plan.get("goal", "Governed dashboard"))}</h1>
          </div>
          <div className="rounded border border-slate-700 px-3 py-2 text-xs text-slate-300">
            {{rows.length}} preview rows from governed artifact
          </div>
        </div>

        {{dashboardPlan.warnings?.length > 0 && (
          <div className="rounded border border-amber-400/40 bg-amber-400/10 p-4 text-sm text-amber-100">
            {{dashboardPlan.warnings.join(" ")}}
          </div>
        )}}

        <div className="grid gap-4 md:grid-cols-3">
          {{dashboardPlan.kpis.map((kpi: any) => (
            <article key={{kpi.name}} className="rounded border border-slate-800 bg-slate-900 p-4">
              <p className="text-xs uppercase text-slate-400">{{kpi.name}}</p>
              <p className="mt-3 text-3xl font-semibold">{{computeMetric(kpi.metric_expression).toLocaleString()}}</p>
              <code className="mt-3 block text-xs text-cyan-200">{{kpi.metric_expression}}</code>
            </article>
          ))}}
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {{dashboardPlan.charts.map((chart: any) => {{
            const expression = metricExpression(chart.metric);
            const data = groupedRows(chart.dimension ?? chart.time_dimension, expression);
            return (
              <article key={{chart.title}} className="rounded border border-slate-800 bg-slate-900 p-4">
                <div className="mb-4 flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-medium">{{chart.title}}</h2>
                    <code className="text-xs text-cyan-200">{{expression}}</code>
                  </div>
                  <span className="text-xs text-slate-400">{{chart.chart_type}}</span>
                </div>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    {{chart.chart_type === "line" ? (
                      <LineChart data={{data}}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="name" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip />
                        <Line type="monotone" dataKey="value" stroke="#22d3ee" strokeWidth={{2}} />
                      </LineChart>
                    ) : (
                      <BarChart data={{data}}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="name" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip />
                        <Bar dataKey="value" fill="#22d3ee" />
                      </BarChart>
                    )}}
                  </ResponsiveContainer>
                </div>
              </article>
            );
          }})}}
        </div>
      </section>
    </main>
  );
}}
'''

    def _artifact_readme(self, plan: dict) -> str:
        return "\n".join(
            [
                "# DashForge Generated Dashboard",
                "",
                f"Goal: {plan.get('goal', 'Governed dashboard')}",
                "",
                "This artifact is generated as editable Next.js code. Metric expressions are embedded plainly",
                "so reviewers can inspect or replace them before production deployment.",
            ]
        )

    def _tsx_text(self, value: str) -> str:
        return re.sub(r"[{}<>]", "", value)

