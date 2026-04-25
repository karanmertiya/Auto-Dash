"use client";

import { useEffect, useState } from "react";

import { JsonInspector } from "@/components/json-inspector";
import { apiGet } from "@/lib/api";

export default function HistoryPage() {
  const [history, setHistory] = useState<any>(null);

  useEffect(() => {
    apiGet("/api/governance/history").then(setHistory);
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold">Version history and audit trail</h1>
        <p className="text-sm text-zinc-600">User actions and system events are recorded for reproducibility.</p>
      </div>
      <section className="rounded border border-line bg-white">
        <header className="border-b border-line px-4 py-3 text-sm font-semibold">Recent actions</header>
        <div className="divide-y divide-line">
          {(history?.user_actions ?? []).map((action: any) => (
            <div key={action.id} className="grid gap-2 px-4 py-3 text-sm md:grid-cols-[160px_220px_1fr]">
              <span className="text-zinc-500">{new Date(action.created_at).toLocaleString()}</span>
              <span className="font-medium">{action.action}</span>
              <span className="font-mono text-xs text-zinc-600">{action.entity_type}:{action.entity_id}</span>
            </div>
          ))}
        </div>
      </section>
      <JsonInspector title="Audit log JSON" value={history} />
    </div>
  );
}

