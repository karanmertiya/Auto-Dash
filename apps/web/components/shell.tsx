import Link from "next/link";
import type { ReactNode } from "react";
import { Activity, Database, FileCode2, GitBranch, LayoutDashboard, Scale, ShieldCheck, UploadCloud } from "lucide-react";

const nav = [
  { href: "/", label: "Upload", icon: UploadCloud },
  { href: "/cleaning", label: "Cleaning", icon: FileCode2 },
  { href: "/semantic", label: "Semantic", icon: Database },
  { href: "/kpi", label: "KPI Plan", icon: Activity },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/history", label: "History", icon: GitBranch }
];

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded bg-zinc-900 text-white">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-zinc-950">DashForge Core</p>
              <p className="text-xs text-zinc-500">Glass-box data-to-dashboard accelerator</p>
            </div>
          </Link>
          <div className="hidden items-center gap-2 rounded border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800 md:flex">
            <ShieldCheck className="h-4 w-4" />
            Raw, cleaned, semantic, and dashboard layers stay separate
          </div>
        </div>
        <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-5 pb-3">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="focus-ring inline-flex items-center gap-2 rounded px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100"
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-7xl px-5 py-6">{children}</main>
    </div>
  );
}
