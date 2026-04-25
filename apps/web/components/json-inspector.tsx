"use client";

import { Copy } from "lucide-react";

export function JsonInspector({ value, title }: { value: unknown; title: string }) {
  const text = JSON.stringify(value, null, 2);
  return (
    <section className="rounded border border-line bg-white">
      <header className="flex items-center justify-between border-b border-line px-4 py-3">
        <h2 className="text-sm font-semibold text-zinc-900">{title}</h2>
        <button
          className="focus-ring rounded border border-zinc-300 p-1.5 text-zinc-700 hover:bg-zinc-50"
          title="Copy JSON"
          onClick={() => navigator.clipboard.writeText(text)}
        >
          <Copy className="h-4 w-4" />
        </button>
      </header>
      <pre className="max-h-[620px] overflow-auto p-4 text-xs leading-5 text-zinc-800">{text}</pre>
    </section>
  );
}

