"use client";

import { Copy } from "lucide-react";

export function CodePanel({
  value,
  onChange,
  title
}: {
  value: string;
  onChange?: (value: string) => void;
  title: string;
}) {
  return (
    <section className="rounded border border-line bg-white">
      <header className="flex items-center justify-between border-b border-line px-4 py-3">
        <h2 className="text-sm font-semibold">{title}</h2>
        <button
          className="focus-ring rounded border border-zinc-300 p-1.5 text-zinc-700 hover:bg-zinc-50"
          title="Copy code"
          onClick={() => navigator.clipboard.writeText(value)}
        >
          <Copy className="h-4 w-4" />
        </button>
      </header>
      <textarea
        className="h-[520px] w-full resize-y border-0 bg-zinc-950 p-4 font-mono text-xs leading-5 text-zinc-100 focus:ring-0"
        value={value}
        onChange={(event) => onChange?.(event.target.value)}
        spellCheck={false}
      />
    </section>
  );
}

