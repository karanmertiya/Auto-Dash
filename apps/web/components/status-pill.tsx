import { AlertTriangle, CheckCircle2, Clock3, XCircle } from "lucide-react";

type Status = "draft" | "profiled" | "executed" | "succeeded" | "failed" | "warning" | "error" | string;

const styles: Record<string, string> = {
  draft: "border-zinc-300 bg-white text-zinc-700",
  profiled: "border-cyan-200 bg-cyan-50 text-cyan-800",
  executed: "border-emerald-200 bg-emerald-50 text-emerald-800",
  succeeded: "border-emerald-200 bg-emerald-50 text-emerald-800",
  failed: "border-red-200 bg-red-50 text-red-800",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  error: "border-red-200 bg-red-50 text-red-800"
};

export function StatusPill({ status }: { status: Status }) {
  const Icon = status === "failed" || status === "error" ? XCircle : status === "warning" ? AlertTriangle : status === "draft" ? Clock3 : CheckCircle2;
  return (
    <span className={`inline-flex items-center gap-1 rounded border px-2 py-1 text-xs ${styles[status] ?? styles.draft}`}>
      <Icon className="h-3.5 w-3.5" />
      {status}
    </span>
  );
}

