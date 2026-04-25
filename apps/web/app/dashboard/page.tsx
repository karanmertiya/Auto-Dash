"use client";

import { useEffect, useState } from "react";
import { Download, FileCode2, LayoutDashboard } from "lucide-react";

import { JsonInspector } from "@/components/json-inspector";
import { apiPost, artifactUrl } from "@/lib/api";

export default function DashboardPage() {
  const [dashboardPlanId, setDashboardPlanId] = useState("");
  const [artifact, setArtifact] = useState<any>(null);

  useEffect(() => {
    setDashboardPlanId(window.localStorage.getItem("dashforge.dashboardPlanId") ?? "");
  }, []);

  async function generate() {
    const next = await apiPost<any>(`/api/dashboards/plans/${dashboardPlanId}/generate`, { actor: "local-user" });
    setArtifact(next);
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold">Dashboard artifact</h1>
        <p className="text-sm text-zinc-600">Generated as editable Next.js code with visible metric logic.</p>
      </div>
      <section className="rounded border border-line bg-white p-4">
        <label className="text-sm font-medium">Dashboard plan ID</label>
        <div className="mt-2 flex flex-wrap gap-2">
          <input className="focus-ring min-w-[320px] flex-1 rounded border-line text-sm" value={dashboardPlanId} onChange={(event) => setDashboardPlanId(event.target.value)} />
          <button className="focus-ring inline-flex items-center gap-2 rounded bg-cyan-700 px-3 py-2 text-sm text-white" onClick={generate}>
            <LayoutDashboard className="h-4 w-4" />
            Generate code
          </button>
          {artifact ? (
            <a className="focus-ring inline-flex items-center gap-2 rounded border border-zinc-300 bg-white px-3 py-2 text-sm" href={artifactUrl(`/api/artifacts/dashboards/${artifact.id}.zip`)}>
              <Download className="h-4 w-4" />
              Export zip
            </a>
          ) : null}
        </div>
      </section>
      {artifact ? (
        <section className="rounded border border-line bg-white p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <FileCode2 className="h-4 w-4 text-cyan-700" />
            Generated files
          </div>
          <div className="space-y-2 text-sm">
            {Object.keys(artifact.metadata_json?.files ?? {}).map((file) => (
              <div key={file} className="rounded border border-line bg-panel px-3 py-2 font-mono text-xs">{file}</div>
            ))}
          </div>
        </section>
      ) : null}
      <JsonInspector title="Dashboard artifact manifest" value={artifact} />
    </div>
  );
}

