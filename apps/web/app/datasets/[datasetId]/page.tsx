"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowRight, ShieldAlert } from "lucide-react";

import { JsonInspector } from "@/components/json-inspector";
import { StatusPill } from "@/components/status-pill";
import { apiGet, apiPost } from "@/lib/api";

export default function DatasetProfilePage() {
  const params = useParams<{ datasetId: string }>();
  const datasetId = params.datasetId;
  const [profile, setProfile] = useState<any>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [validation, setValidation] = useState<any>(null);

  useEffect(() => {
    window.localStorage.setItem("dashforge.datasetId", datasetId);
    apiGet(`/api/datasets/${datasetId}/profile`).then(setProfile);
    apiGet<any[]>(`/api/datasets/${datasetId}/versions`).then(setVersions);
  }, [datasetId]);

  async function runValidation() {
    setValidation(await apiPost(`/api/validation/datasets/${datasetId}`));
  }

  const columns = profile?.columns ?? [];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Profile inspection</h1>
          <p className="text-sm text-zinc-600">{profile?.row_count ?? 0} rows, {profile?.column_count ?? 0} columns, raw layer preserved</p>
        </div>
        <div className="flex gap-2">
          <button className="focus-ring rounded bg-zinc-900 px-3 py-2 text-sm text-white" onClick={runValidation}>Validate</button>
          <Link className="focus-ring inline-flex items-center gap-2 rounded bg-cyan-700 px-3 py-2 text-sm text-white" href="/cleaning">
            Cleaning <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>

      {validation?.findings?.length ? (
        <section className="rounded border border-line bg-white">
          <header className="flex items-center gap-2 border-b border-line px-4 py-3 text-sm font-semibold">
            <ShieldAlert className="h-4 w-4 text-amber-600" />
            Validation findings
          </header>
          <div className="divide-y divide-line">
            {validation.findings.map((finding: any) => (
              <div key={`${finding.rule_name}-${finding.message}`} className="grid gap-2 px-4 py-3 text-sm md:grid-cols-[120px_220px_1fr]">
                <StatusPill status={finding.severity} />
                <span className="font-medium">{finding.rule_name}</span>
                <span className="text-zinc-700">{finding.message}</span>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="rounded border border-line bg-white">
        <header className="border-b border-line px-4 py-3 text-sm font-semibold">Column profile</header>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
              <tr>
                <th className="px-4 py-3">Column</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Missing</th>
                <th className="px-4 py-3">Distinct</th>
                <th className="px-4 py-3">Warnings</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {columns.map((column: any) => (
                <tr key={column.name}>
                  <td className="px-4 py-3 font-medium">{column.name}</td>
                  <td className="px-4 py-3 text-zinc-600">{column.inferred_type}</td>
                  <td className="px-4 py-3">{column.semantic_role}</td>
                  <td className="px-4 py-3">{Math.round((column.stats?.missing_ratio ?? 0) * 1000) / 10}%</td>
                  <td className="px-4 py-3">{column.stats?.distinct_count}</td>
                  <td className="px-4 py-3 text-amber-800">{column.warnings?.join(" ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-2">
        <JsonInspector title="Structured profile JSON" value={profile} />
        <JsonInspector title="Dataset versions" value={versions} />
      </div>
    </div>
  );
}

